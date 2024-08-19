use std::{collections::HashMap};

use crate::{action::Action, qos::Qos, state::State, types::{parameter::HYPER_PARAMETER, state::Color}, CtlRes, CtlState, DecSolver, HisQos};

use super::{checker::determine_forward_switch, foward_switch_solver::forward_predict};


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
                let tx_parts = ChannelBalanceSolver::new().solve_by_rtt_balance(qos.clone(), his_qoses, name.clone());
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
    max_step: f64,
    epsilon_rtt: f64,
    scale_factor: f64,
    epsilon_prob_upper: f64,
    epsilon_prob_lower: f64,
    redundency_mode: bool,
}

impl ChannelBalanceSolver {
    pub fn new() -> Self {
        ChannelBalanceSolver {
            inc_direction: [-1, 1],
            min_step: 0.05,
            max_step: HYPER_PARAMETER.scale_factor * HYPER_PARAMETER.balance_channel_rtt_thres / HYPER_PARAMETER.epsilon_rtt,
            epsilon_rtt: HYPER_PARAMETER.epsilon_rtt,
            scale_factor: HYPER_PARAMETER.scale_factor,
            epsilon_prob_upper: 0.6,
            epsilon_prob_lower: 0.01,
            redundency_mode: false,
        }
    }

    pub fn control(&mut self, qos: Qos, his_qoses: &HisQos, name: String) -> Vec<f64> {
        if self.redundency_mode {
            self.redundency_balance(qos)
        } else {
            self.solve_by_rtt_balance(qos, his_qoses, name)
        }
    }

    fn solve_by_rtt_balance(&mut self, qos: Qos, his_qoses: &HisQos, name: String) -> Vec<f64> {
        let mut tx_parts = qos.tx_parts.clone();

        if let (Some(channel_rtts), Some(_rtt)) = (qos.channel_rtts, qos.rtt){

            let diff = match tx_parts.iter().any( |&x| x == 0.0 || x == 1.0) {
                true => HYPER_PARAMETER.balance_channel_rtt_thres, // control the initial step
                false => (channel_rtts[0] - channel_rtts[1]).abs(),
            };

            if diff <= self.epsilon_rtt {
                return tx_parts;
            }
            else if diff <= HYPER_PARAMETER.balance_channel_rtt_thres{
                let step = self.min_step * self.scale_factor * diff / self.epsilon_rtt;
                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -step } else { step };
                tx_parts[0] = format!("{:.2}", tx_parts[0].clamp(0.0, 1.0)).parse().unwrap();
                tx_parts[1] = tx_parts[0];
                return tx_parts;
            }
            else if determine_forward_switch(his_qoses, &name) {
                return forward_predict(his_qoses, &name);
            }
            else {
                let step = self.max_step;
                tx_parts[0] += if channel_rtts[0] > channel_rtts[1] { -step } else { step };
                tx_parts[0] = format!("{:.2}", tx_parts[0].clamp(0.0, 1.0)).parse().unwrap();
                tx_parts[1] = tx_parts[0];
                return tx_parts;
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