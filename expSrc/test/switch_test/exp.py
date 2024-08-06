from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import channelBalanceSolver, channelSwitchSolver
from util import stream
from typing import List
from schema import Schema, And, Use, Optional, Or
import os, json

import util.constHead as constHead

TARGET_RTT = 16


def test_when_channel1_is_bad():
    channel_switch_solver   = channelSwitchSolver(TARGET_RTT)
    channel_switch_solver.switch_state = constHead.MUL_CHAN
    print("Test when channel1 is bad")
    tx_parts = [0.5, 0.5]
    rtt      = [18, 5]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

    tx_parts = [0.5, 0.5]
    rtt      = [19, 5]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

def test_when_channel2_is_bad():
    channel_switch_solver   = channelSwitchSolver(TARGET_RTT)
    channel_switch_solver.switch_state = constHead.MUL_CHAN
    print("Test when channel2 is bad")
    tx_parts = [0.5, 0.5]
    rtt      = [5, 18]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

    tx_parts = [0.5, 0.5]
    rtt      = [5, 19]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

def test_when_channel_1_is_bad_single_channel():
    channel_switch_solver   = channelSwitchSolver(TARGET_RTT)
    print("Test when channel1 is bad, channel 1 started")
    tx_parts = [0, 0]
    rtt      = [18, 0]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

    tx_parts = [0, 0]
    rtt      = [19, 0]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

def test_when_channel2_is_good():
    channel_switch_solver   = channelSwitchSolver(TARGET_RTT)
    channel_switch_solver.switch_state = constHead.MUL_CHAN
    channel_switch_solver.islog = True
    print("Test when channel 2 is good")
    tx_parts = [0.5, 0.5]
    rtt      = [15, 5]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

    tx_parts = [0.6, 0.6]
    rtt      = [13, 6]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)
    
def test_when_channel1_is_good():
    channel_switch_solver   = channelSwitchSolver(TARGET_RTT)
    channel_switch_solver.switch_state = constHead.MUL_CHAN
    channel_switch_solver.islog = True
    print("Test when channel 1 is good")
    tx_parts = [0.5, 0.5]
    rtt      = [7, 5]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

    tx_parts = [0.6, 0.6]
    rtt      = [6, 15]

    print(channel_switch_solver.switch(tx_parts, rtt).switch_state)

test_when_channel1_is_bad()

test_when_channel2_is_bad()

test_when_channel_1_is_bad_single_channel()

test_when_channel2_is_good()

test_when_channel1_is_good()