#include "rclcpp/rclcpp.hpp"
#include "uclv_tactile_interfaces/msg/tactile_stamped.hpp"
#include "uclv_tactile_interfaces/action/compute_bias.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include <vector>
#include <string>


using ComputeBias = uclv_tactile_interfaces::action::ComputeBias;
using TactileStamped = uclv_tactile_interfaces::msg::TactileStamped;
using namespace std::placeholders;

class ComputeBiasActionServer : public rclcpp::Node {
public:
    ComputeBiasActionServer() : Node("remove_bias"), b_msg_arrived(false), b_can_pub(false) 
    {
        // Input Parameters
        this->declare_parameter("in_voltage_topic", "tactile_voltage/raw");
        this->declare_parameter("out_voltage_topic", "tactile_voltage/rect");
        this->declare_parameter("action_compute_bias", "tactile_voltage/action_compute_bias");
        this->declare_parameter("default_num_samples", 100);
        this->declare_parameter("num_voltages", 25);

        this->get_parameter("in_voltage_topic", in_voltage_topic_str);
        this->get_parameter("out_voltage_topic", out_voltage_topic_str);
        this->get_parameter("action_compute_bias", action_compute_bias_str);
        this->get_parameter("default_num_samples", default_num_samples_to_use);
        this->get_parameter("num_voltages", NUM_V);

        // Initialization variables
        bias.resize(NUM_V, 0.0);
        raw_valtages.resize(NUM_V, 0.0);

        // Subscriber, Publisher e Action Server
        subVoltage = this->create_subscription<TactileStamped>(in_voltage_topic_str, 1, std::bind(&ComputeBiasActionServer::readV, this, _1));
        pubV = this->create_publisher<TactileStamped>(out_voltage_topic_str, 1);

        compute_bias_as = rclcpp_action::create_server<ComputeBias>(
            this,
            action_compute_bias_str,
            std::bind(&ComputeBiasActionServer::handleGoal, this, _1, _2),
            std::bind(&ComputeBiasActionServer::handleCancel, this, _1),
            std::bind(&ComputeBiasActionServer::handleAccepted, this, _1)
        );

        RCLCPP_INFO(this->get_logger(), "Waiting for initial voltages...");
        waitForVoltage();

        // First computation of the bias
        done = false;
        while (rclcpp::ok() && !computeBias(default_num_samples_to_use)) {
            RCLCPP_ERROR(this->get_logger(), "Retrying bias computation...");
        }
        done = true;
        b_can_pub = true;
    }

private:

    // Attributes
    rclcpp::Publisher<TactileStamped>::SharedPtr pubV;
    rclcpp::Subscription<TactileStamped>::SharedPtr subVoltage;
    rclcpp_action::Server<ComputeBias>::SharedPtr compute_bias_as;

    // Attributes to manage the bias computation
    std::string in_voltage_topic_str, out_voltage_topic_str, action_compute_bias_str;
    std::vector<float> bias, raw_valtages;
    bool b_msg_arrived, b_can_pub;
    int default_num_samples_to_use, NUM_V;
    //! variable to avoid multiple calls to spin_some
    bool done;

    static constexpr int NUM_SAMPLES_NOT_USE = 10;
    static constexpr int MAX_WAIT_COUNT = 100;
    static constexpr double TIME_TO_SLEEP_WAITING_SAMPLE = 0.01;

    // Callback to read and publish the voltages
    void readV(const TactileStamped::SharedPtr msg) {
        raw_valtages = msg->tactile.data;
        for (int i = 0; i < NUM_V; i++) {
            msg->tactile.data[i] -= bias[i];
        }
        b_msg_arrived = true;
        if (b_can_pub) {
            pubV->publish(*msg);
        }
    }

    // Compute the bias
    bool computeBias(int num_samples_to_use) {
        std::vector<double> bias_sum(NUM_V, 0.0);
        RCLCPP_INFO(this->get_logger(), "Computing bias...");

        for (int i = 0; i < num_samples_to_use; ++i) {
            b_msg_arrived = false;
            int wait_count = 0;
            while (!b_msg_arrived && wait_count < MAX_WAIT_COUNT) {
                rclcpp::sleep_for(std::chrono::milliseconds(int(TIME_TO_SLEEP_WAITING_SAMPLE * 1000)));
                if(!done)
                    rclcpp::spin_some(this->get_node_base_interface());
                wait_count++;
            }
            if (!b_msg_arrived) return false;

            for (int j = 0; j < NUM_V; ++j) {
                bias_sum[j] += raw_valtages[j];
            }
        }

        for (int i = 0; i < NUM_V; ++i) {
            bias[i] = bias_sum[i] / num_samples_to_use;
        }

        RCLCPP_INFO(this->get_logger(), "Bias computation DONE!");
        return true;
    }

    // Callbacks for the action server
    rclcpp_action::GoalResponse handleGoal(const rclcpp_action::GoalUUID & uuid, std::shared_ptr<const ComputeBias::Goal> goal) {
        RCLCPP_INFO(this->get_logger(), "Received goal request with num_samples: %d", goal->num_samples);
        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
    }

    rclcpp_action::CancelResponse handleCancel(const std::shared_ptr<rclcpp_action::ServerGoalHandle<ComputeBias>> goal_handle) {
        RCLCPP_INFO(this->get_logger(), "Cancel request received");
        return rclcpp_action::CancelResponse::ACCEPT;
    }

    void handleAccepted(const std::shared_ptr<rclcpp_action::ServerGoalHandle<ComputeBias>> goal_handle) {
        std::thread{std::bind(&ComputeBiasActionServer::executeComputeBiasCB, this, _1), goal_handle}.detach();
    }

    void executeComputeBiasCB(const std::shared_ptr<rclcpp_action::ServerGoalHandle<ComputeBias>> goal_handle) {
        const auto goal = goal_handle->get_goal();
        auto remove_bias_result = std::make_shared<uclv_tactile_interfaces::action::ComputeBias_Result>();
        remove_bias_result->success = computeBias(goal->num_samples > 0 ? goal->num_samples : default_num_samples_to_use);
        goal_handle->succeed(remove_bias_result);
    }

    void waitForVoltage() {
        b_msg_arrived = false;
        while (rclcpp::ok() && !b_msg_arrived) {
            rclcpp::spin_some(this->get_node_base_interface());
            rclcpp::sleep_for(std::chrono::milliseconds(int(TIME_TO_SLEEP_WAITING_SAMPLE * 1000)));
        }
    }

};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ComputeBiasActionServer>());
    rclcpp::shutdown();
    return 0;
}
