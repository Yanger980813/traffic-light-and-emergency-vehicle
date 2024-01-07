import os
import sys
import time
sys.path.append('/mnt/c/ns2/sumo/tools')
import optparse
import traci

def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true", default=False, help="Run the command line version of SUMO")
    options, args = opt_parser.parse_args()
    return options

def get_traffic_light_id(lane_id):
    traffic_lights = traci.trafficlight.getIDList()
    for traffic_light_id in traffic_lights:
        controlled_lanes = traci.trafficlight.getControlledLanes(traffic_light_id)
        if lane_id in controlled_lanes:
            return traffic_light_id
    return None

def set_traffic_light_state(traffic_light_id, state):
    traci.trafficlight.setRedYellowGreenState(traffic_light_id, state)

def get_all_traffic_light_states():
    traffic_light_states = {}
    traffic_lights = traci.trafficlight.getIDList()
    for traffic_light_id in traffic_lights:
        state = traci.trafficlight.getRedYellowGreenState(traffic_light_id)
        traffic_light_states[traffic_light_id] = state
    return traffic_light_states

def set_all_traffic_lights_states(states):
    for traffic_light_id, state in states.items():
        set_traffic_light_state(traffic_light_id, state)

def set_all_other_lanes_red(current_lane_id):
    traffic_lights = traci.trafficlight.getIDList()
    for traffic_light_id in traffic_lights:
        controlled_lanes = traci.trafficlight.getControlledLanes(traffic_light_id)
        for lane_id in controlled_lanes:
            if lane_id != current_lane_id:
                set_traffic_light_state(traffic_light_id, "rrrrrrrrrrrr")

def set_traffic_light_logic(traffic_light_id, program_id):
    traci.trafficlight.setProgram(traffic_light_id, program_id)

def set_all_traffic_lights_to_original_logic():
    original_logic = {
        "j2": "0",
        "j5": "0",
        "j7": "0"
    }
    for traffic_light_id, program_id in original_logic.items():
        set_traffic_light_logic(traffic_light_id, program_id)

def run():
    step = 0
    emergency_vehicle_present = False
    revert_time = None
    desired_logic_set = False

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            print("Step:", step)

            emergency_vehicle_present = any(traci.vehicle.getTypeID(vehicle_id) == "ev" for vehicle_id in traci.vehicle.getIDList())
            print("Emergency Vehicle Present:", emergency_vehicle_present)

            # Handle traffic lights when emergency vehicle is present
            if emergency_vehicle_present:
                emergency_vehicle_id = [vehicle_id for vehicle_id in traci.vehicle.getIDList() if traci.vehicle.getTypeID(vehicle_id) == "ev"][0]
                lane_id = traci.vehicle.getLaneID(emergency_vehicle_id)
                print("Lane ID of Emergency Vehicle:", lane_id)

                traffic_light_id = get_traffic_light_id(lane_id)
                if traffic_light_id:
                    print("Traffic light controlling lane {} is {}".format(lane_id, traffic_light_id))

                    # Set the traffic light to green
                    set_traffic_light_state(traffic_light_id, "GGGGGGGGGGGG")
                    print("Traffic light set to green for lane {}".format(lane_id))

                    # Set all other lanes to red
                    set_all_other_lanes_red(lane_id)
                    print("All other lanes set to red")

            # Handle reverting traffic lights and setting to desired logic
            elif time.time() > revert_time:
                # Revert all traffic lights to the desired logic
                if not desired_logic_set:
                    set_all_traffic_lights_to_original_logic()
                    print("Set all traffic lights to original logic")
                    desired_logic_set = True

                # Wait for a while and then reset the variables
                if step % 300 == 0:  # 300 steps at 1 step/s is 300 seconds
                    revert_time = time.time() + 5
                    desired_logic_set = False

            step += 1

    except (traci.exceptions.FatalTraCIError, KeyboardInterrupt) as e:
        print("Error: {}".format(e))
    finally:
        traci.close()
        sys.stdout.flush()

if __name__ == "__main__":
    options = get_options()
    sumo_binary = "sumo-gui" if not options.nogui else "sumo"
    traci.start([sumo_binary, "-c", "demo1.sumo.cfg", "--tripinfo-output", "tripinfo.xml"])
    run()
