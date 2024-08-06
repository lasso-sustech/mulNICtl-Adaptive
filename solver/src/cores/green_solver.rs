use std::{collections::HashMap};

use crate::{action::Action, qos::Qos, state::State, types::state::Color, CtlRes, CtlState, DecSolver};


pub struct GSolver {
    #[warn(dead_code)]
    pub backward_threshold: f64,
    pub is_all_balance: bool,
    pub throttle_step_size: f64,
}

#[allow(dead_code)]
impl GSolver {
    pub fn new() -> Self {
        GSolver {
            backward_threshold: 0.8,
            is_all_balance: false,
            throttle_step_size: 10.0,
        }
    }
}

impl DecSolver for GSolver{
    fn control(&self, his_qoses: &Vec<HashMap<String, Qos>>, channel_state: &State) -> CtlRes {
        let qoses = his_qoses.last().unwrap();
        let controls: HashMap<String, Action> = qoses.into_iter().map(|(name, qos)| {
            let channel_colors: Vec<Color>  = qos.channels.iter()
                .filter_map(|channel| channel_state.color.get(channel).cloned())
                .collect();
            if qos.channel_rtts.is_some(){
                let max_his_rtt = get_max_his_rtt(his_qoses, name, 10);
                let tx_parts = ChannelBalanceSolver::new(self.is_all_balance).solve_by_rtt_balance(qos.clone(), channel_state, max_his_rtt);
                (name.clone(), Action::new(Some(tx_parts), None, Some(channel_colors)))
            }
            else{
                let mut throttle = qos.throttle + self.throttle_step_size;
                if throttle <= 0.0 {
                    throttle = 1.0;
                } else if throttle >= 1000.0 {
                    throttle = 1000.0;
                }
                (name.clone(), Action::new(None, Some(throttle), Some(channel_colors)))
            }
        }).collect();
        let ctrl_state = CtlState::Normal;
        (controls, ctrl_state, None)

    }
}

fn get_max_his_rtt(his_qoses: &Vec<HashMap<String, Qos>>, qos_name: &String, qos_range: usize) -> [f64; 2] {
    let mut max_rtt = [0.0, 0.0];
    // traverse inverse qos_range
    let minimum_range = his_qoses.len() - his_qoses.len().min(qos_range as usize);
    for i in (minimum_range..his_qoses.len()) {
        if let Some(qos) = his_qoses[i].get(qos_name) {
            if let Some(channel_rtts) = qos.channel_rtts.clone() {
                for (idx, &rtt) in channel_rtts.iter().enumerate() {
                    if rtt > max_rtt[idx] {
                        max_rtt[idx] = rtt;
                    }
                }
            }
        }
    }
    max_rtt
}

pub struct ChannelBalanceSolver {
    inc_direction: [i32; 2],
    min_step: f64,
    epsilon_rtt: f64,
    epsilon_prob_upper: f64,
    epsilon_prob_lower: f64,
    redundency_mode: bool,
    is_all_balance: bool,
}

impl ChannelBalanceSolver {
    fn new(is_all_balance: bool) -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            epsilon_rtt: 0.002,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
            is_all_balance: is_all_balance,
        }
    }

    fn solve_by_rtt_balance(&mut self, qos: Qos, channel_state: &State, last_val: [f64; 2]) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();


        if let Some(channel_rtts) = qos.channel_rtts {
            if !self.is_all_balance && qos.tx_parts.iter().any(|&tx_part| tx_part == 0.0 || tx_part == 1.0) {
                return tx_parts;
            }

            if channel_rtts[0] <= 0.012 && channel_rtts[1] == 0.0 {
                return tx_parts;
            }

            if channel_rtts[1] == 0.0 && channel_rtts[0] <= last_val[1] {
                return tx_parts;
            }

            if (channel_rtts[0] - channel_rtts[1]).abs() > self.epsilon_rtt {
                let direction = if channel_rtts[0] > channel_rtts[1] { 1 } else { 0 };

                // if the direction is toward yellow or red channel, stop it
                // if channel_state.color.get(&qos.channels[direction]).cloned() == Some(Color::Red) {
                //     return tx_parts;
                // }

                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -self.min_step } else { self.min_step };
                // tx_parts[0] = format!("{:.2}", tx_parts[0].clamp(0.0, 1.0)).parse().unwrap();
                tx_parts[1] = tx_parts[0];
            }
        }

        tx_parts
    }

    fn redundency_balance(&mut self, qos: Qos) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();
        if let Some(channel_probabilities) = qos.channel_probabilities {
            for (idx, &pro) in channel_probabilities.iter().enumerate() {
                assert!((0.0..=1.0).contains(&pro), "Invalid probability: {}, should be in [0, 1]", pro);
                if pro > self.epsilon_prob_upper {
                    tx_parts[idx] += self.min_step * self.inc_direction[idx] as f64;
                } else if pro < self.epsilon_prob_lower {
                    tx_parts[idx] -= self.min_step * self.inc_direction[idx] as f64;
                }
                tx_parts[idx] = (tx_parts[idx].max(0.0).min(1.0) * 100.0).round() / 100.0;
            }
        }

        tx_parts
    }
}