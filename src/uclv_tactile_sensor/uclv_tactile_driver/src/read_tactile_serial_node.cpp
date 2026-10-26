#include <rclcpp/rclcpp.hpp>
#include "serial/serial.h"
#include <std_msgs/msg/header.hpp>
#include "uclv_tactile_interfaces/msg/tactile_stamped.hpp"    

#define ERROR_COLOR     "\033[1m\033[31m"      /* Bold Red */
#define WARN_COLOR      "\033[1m\033[33m"      /* Bold Yellow */
#define SUCCESS_COLOR   "\033[1m\033[32m"      /* Bold Green */
#define CRESET          "\033[0m"
#define CHAR_TO_SEND    'a'

using namespace std;

void set_serial_low_latency(const string& serial_port)
{
  cout << "Setting low_latency for " << WARN_COLOR << serial_port << CRESET << endl;
  string command = "setserial " + serial_port + " low_latency";
  int result = system(command.c_str());
  cout << "Setting low_latency for " << WARN_COLOR << serial_port << CRESET << " result:" << WARN_COLOR << result << CRESET << endl;
}

//==============MAIN================//

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>("read_tactile_serial");

    node->declare_parameter<std::string>("serial_port", "/dev/ttyUSB0");
    node->declare_parameter<int>("baud_rate", 1000000);
    node->declare_parameter<int>("serial_timeout", 1000);
    node->declare_parameter<int>("rows", 5);
    node->declare_parameter<int>("cols", 5);
    node->declare_parameter<std::string>("frame_id", "fingertip0");
    node->declare_parameter<std::string>("tf_prefix", "");
    node->declare_parameter<std::string>("output_topic", "tactile_voltage/raw");

    /**** CHECK PARAMS ****/
    std::string serial_port, frame_id, tf_prefix, topic_name;
    int baud_rate, serial_timeout, num_rows, num_cols;

    node->get_parameter("serial_port", serial_port);
    node->get_parameter("baud_rate", baud_rate);
    node->get_parameter("serial_timeout", serial_timeout);
    node->get_parameter("rows", num_rows);
    node->get_parameter("cols", num_cols);
    node->get_parameter("frame_id", frame_id);
    node->get_parameter("tf_prefix", tf_prefix);
    node->get_parameter("output_topic", topic_name);

    /**** INIT SERIAL ****/	
    set_serial_low_latency(serial_port);
    serial::Serial my_serial(serial_port, baud_rate, serial::Timeout::simpleTimeout(serial_timeout));

    /**** CHECK ****/
    if(!my_serial.isOpen()){
   	    cout << ERROR_COLOR << "ERROR - SERIAL PORT " << WARN_COLOR << serial_port << ERROR_COLOR << " is not open!" << CRESET <<endl;
   	    exit(-1);
    }
    cout << SUCCESS_COLOR << "SERIAL PORT " << WARN_COLOR << serial_port << SUCCESS_COLOR << " OPEN - OK" << CRESET << endl;

    // ==== Tactile msg ====
    double voltages_count = num_rows*num_cols;
    auto finger_voltages = uclv_tactile_interfaces::msg::TactileStamped();
    finger_voltages.header.stamp = node->get_clock()->now();
    finger_voltages.header.frame_id = tf_prefix+frame_id;
    finger_voltages.tactile.data.resize(voltages_count);
    finger_voltages.tactile.rows = num_rows;
    finger_voltages.tactile.cols = num_cols;
    finger_voltages.tactile.info = "voltages";

    // PUBLISHER
    auto pubTactile = node->create_publisher<uclv_tactile_interfaces::msg::TactileStamped>(topic_name, 10);

    // init buffers
    const int dim_buffer = voltages_count*2;
    uint8_t b2write[1], readBytes[dim_buffer];
    b2write[0] = CHAR_TO_SEND;


    /**** ROS MAIN LOOP  ****/
    while(rclcpp::ok())
    {   
        my_serial.write(b2write,1);
        my_serial.read(readBytes, dim_buffer);
        finger_voltages.header.stamp = node->get_clock()->now();
            
        for (int i = 0; i < voltages_count; i++) 
        {
            finger_voltages.tactile.data[i] = (double)(readBytes[i*2] + (readBytes[i*2+1]&0b00001111)*256) * 3.3/4096.0;
        }
        
        pubTactile->publish(finger_voltages);	
    }

    return 0;

}
