use crate::{types::parameter::HYPER_PARAMETER, HisQos};

pub fn determine_forward_switch(his_qoses: &HisQos, task: &String) -> bool {
    let len = his_qoses.len();
    let start = if len >= HYPER_PARAMETER.balance_time_thres {
        len - HYPER_PARAMETER.balance_time_thres
    } else {
        0
    };
    
    // Iterate over each task to determine if switching is necessary.
    let mut min_tx = f64::MAX;
    let mut max_tx = f64::MIN;
    let mut min_idx = start;
    let mut max_idx = start;

    // Find the minimum and maximum tx_parts for the task across the given range.
    for i in start..len {
        if let Some(qos) = his_qoses[i].get(task) {
            let tx_part = qos.tx_parts[0];
            if tx_part < min_tx {
                min_tx = tx_part;
                min_idx = i;
            }
            if tx_part > max_tx {
                max_tx = tx_part;
                max_idx = i;
            }
        }
    }

    // Check if the difference in tx_parts exceeds the threshold.
    if max_tx - min_tx >= HYPER_PARAMETER.balance_tx_part_thres {
        let qos_min = his_qoses[min_idx]
            .get(task)
            .expect("QoS data should be available for min_idx");
        let qos_max = his_qoses[max_idx]
            .get(task)
            .expect("QoS data should be available for max_idx");

        // Ensure both QoS have channel_rtts.
        let channel_rtts_min = qos_min
            .channel_rtts
            .as_ref()
            .expect("channel_rtts must be Some for all Qos instances");
        let channel_rtts_max = qos_max
            .channel_rtts
            .as_ref()
            .expect("channel_rtts must be Some for all Qos instances");

        // Calculate the RTT differences for the channels.
        let rtt_diff_0 = (channel_rtts_min[0] - channel_rtts_max[0]).abs();
        let rtt_diff_1 = (channel_rtts_min[1] - channel_rtts_max[1]).abs();

        // Check if the RTT differences exceed the threshold.
        if rtt_diff_0 >= HYPER_PARAMETER.balance_rtt_thres || rtt_diff_1 >= HYPER_PARAMETER.balance_rtt_thres {
            return true;
        }
    }

    false
}
