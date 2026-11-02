#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "uclv_tactile_interfaces/msg/tactile_stamped.hpp"
#include "uclv_tactile_interfaces/action/compute_bias.hpp"

#include <vector>
#include <string>
#include <mutex>
#include <thread>
#include <chrono>

using ComputeBias = uclv_tactile_interfaces::action::ComputeBias;
using TactileStamped = uclv_tactile_interfaces::msg::TactileStamped;
using namespace std::placeholders;

class ComputeBiasActionServer : public rclcpp::Node {
public:
    ComputeBiasActionServer() : Node("remove_bias"), b_msg_arrived(false), b_can_pub(false) 
    {
        this->declare_parameter("in_voltage_topic", "tactile_voltage/raw");
        this->declare_parameter("out_voltage_topic", "tactile_voltage/rect");
        this->declare_parameter("action_compute_bias", "compute_bias_action");
        this->declare_parameter("default_num_samples", 100);
        this->declare_parameter("num_voltages", 25);

        this->get_parameter("in_voltage_topic", in_voltage_topic_str);
        this->get_parameter("out_voltage_topic", out_voltage_topic_str);
        this->get_parameter("action_compute_bias", action_compute_bias_str);
        this->get_parameter("default_num_samples", default_num_samples_to_use);
        this->get_parameter("num_voltages", NUM_V);

        bias.resize(NUM_V, 0.0f);
        raw_voltages.resize(NUM_V, 0.0f);

        subVoltage = this->create_subscription<TactileStamped>(
            in_voltage_topic_str, 10, std::bind(&ComputeBiasActionServer::readV, this, _1));
        pubV = this->create_publisher<TactileStamped>(out_voltage_topic_str, 10);

        compute_bias_as = rclcpp_action::create_server<ComputeBias>(
            this,
            action_compute_bias_str,
            std::bind(&ComputeBiasActionServer::handleGoal, this, _1, _2),
            std::bind(&ComputeBiasActionServer::handleCancel, this, _1),
            std::bind(&ComputeBiasActionServer::handleAccepted, this, _1)
        );

        RCLCPP_INFO(this->get_logger(), "Nodo remove_bias avviato su action '%s'.", action_compute_bias_str.c_str());

        // Timer per lanciare la tara iniziale in background a spin() attivo
        init_timer_ = this->create_wall_timer(
            std::chrono::milliseconds(50),
            std::bind(&ComputeBiasActionServer::onInitTimer, this)
        );
    }

private:
    rclcpp::Publisher<TactileStamped>::SharedPtr pubV;
    rclcpp::Subscription<TactileStamped>::SharedPtr subVoltage;
    rclcpp_action::Server<ComputeBias>::SharedPtr compute_bias_as;
    rclcpp::TimerBase::SharedPtr init_timer_;

    std::string in_voltage_topic_str, out_voltage_topic_str, action_compute_bias_str;
    std::vector<float> bias, raw_voltages;
    bool b_msg_arrived, b_can_pub;
    int default_num_samples_to_use, NUM_V;

    std::mutex data_mutex_;

    static constexpr int MAX_WAIT_COUNT = 100;
    static constexpr double TIME_TO_SLEEP_WAITING_SAMPLE = 0.01; // 10ms

    void onInitTimer() {
        init_timer_->cancel();

        // Lancia il calcolo della tara in un THREAD SEPARATO per non bloccare lo SingleThreadedExecutor!
        std::thread([this]() {
            RCLCPP_INFO(this->get_logger(), "In attesa dei dati da %s per la tara iniziale...", in_voltage_topic_str.c_str());
            
            // Loop di tentativo finche non raccoglie 100 campioni validi
            while (rclcpp::ok() && !computeBias(default_num_samples_to_use)) {
                RCLCPP_WARN(this->get_logger(), "In attesa che il sensore pubblichi dati su %s...", in_voltage_topic_str.c_str());
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
            }

            if (rclcpp::ok()) {
                b_can_pub = true;
                RCLCPP_INFO(this->get_logger(), "Tara iniziale COMPLETATA! Pubblicazione su %s ABILITATA.", out_voltage_topic_str.c_str());
            }
        }).detach();
    }

    void readV(const TactileStamped::SharedPtr msg) {
        if (static_cast<int>(msg->tactile.data.size()) != NUM_V) return;

        std::lock_guard<std::mutex> lock(data_mutex_);
        raw_voltages = msg->tactile.data;
        
        auto rect_msg = *msg;
        for (int i = 0; i < NUM_V; i++) {
            rect_msg.tactile.data[i] -= bias[i];
        }

        b_msg_arrived = true;
        if (b_can_pub) {
            pubV->publish(rect_msg);
        }
    }

    bool computeBias(int num_samples_to_use) {
        std::vector<double> bias_sum(NUM_V, 0.0);

        for (int i = 0; i < num_samples_to_use; ++i) {
            {
                std::lock_guard<std::mutex> lock(data_mutex_);
                b_msg_arrived = false;
            }

            int wait_count = 0;
            while (wait_count < MAX_WAIT_COUNT) {
                std::this_thread::sleep_for(std::chrono::milliseconds(int(TIME_TO_SLEEP_WAITING_SAMPLE * 1000)));
                std::lock_guard<std::mutex> lock(data_mutex_);
                if (b_msg_arrived) break;
                wait_count++;
            }

            std::lock_guard<std::mutex> lock(data_mutex_);
            if (!b_msg_arrived) {
                return false;
            }

            for (int j = 0; j < NUM_V; ++j) {
                bias_sum[j] += raw_voltages[j];
            }
        }

        std::lock_guard<std::mutex> lock(data_mutex_);
        for (int i = 0; i < NUM_V; ++i) {
            bias[i] = static_cast<float>(bias_sum[i] / num_samples_to_use);
        }

        return true;
    }

    rclcpp_action::GoalResponse handleGoal(const rclcpp_action::GoalUUID & uuid, std::shared_ptr<const ComputeBias::Goal> goal) {
        (void)uuid;
        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
    }

    rclcpp_action::CancelResponse handleCancel(const std::shared_ptr<rclcpp_action::ServerGoalHandle<ComputeBias>> goal_handle) {
        (void)goal_handle;
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
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ComputeBiasActionServer>());
    rclcpp::shutdown();
    return 0;
}