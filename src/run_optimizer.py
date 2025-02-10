from examples.gsopt.milp_optimizer import MilpOptimizer
from examples.gsopt.models import (
    OptimizationWindow, Satellite, GroundStationProvider, GroundStation
)
from examples.gsopt.milp_objectives import MinCostObjective, MinMaxContactGapObjective, MaxDataDownlinkObjective
from brahe import Epoch
import json

def read_tle_file(filename):
    satellites = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    # Process three lines at a time (name and two TLE lines)
    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            break
            
        name = lines[i].strip()
        tle1 = lines[i + 1].strip()
        tle2 = lines[i + 2].strip()
        
        # Create satellite object
        satellite = Satellite(
            name=name,
            satcat_id=tle1[2:7],  # Extract NORAD ID from TLE
            tle_line1=tle1,
            tle_line2=tle2
        )
        satellites.append(satellite)
    
    return satellites

# Your main execution code here
if __name__ == "__main__":
    # Create optimization window
    opt_window = OptimizationWindow(
        sim_start=Epoch("2024-01-01T00:00:00Z"),
        sim_end=Epoch("2024-01-02T00:00:00Z"),
        opt_start=Epoch("2024-01-01T00:00:00Z"),
        opt_end=Epoch("2024-01-02T00:00:00Z")
    )

    # Initialize optimizer
    optimizer = MilpOptimizer(opt_window)
    
    # Load Azure ground stations
    with open('src/examples/data/groundstations/azure.json', 'r') as f:
        azure_data = json.load(f)
        
        # Create a complete provider GeoJSON with all stations
        provider_feature = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Add provider as first feature
        provider_feature["features"].append({
            "type": "Feature",
            "properties": {
                "name": "Azure",
                "provider": "Azure",
                "integration_cost": 10000.0,
                "setup_cost": 5000.0,
                "monthly_cost": 1000.0,
                "cost_per_minute": 1.0,
                "cost_per_pass": 10.0,
                "per_satellite_license_cost": 1000.0,
                "antennas": 1
            },
            "geometry": {
                "type": "Point",
                "coordinates": [0, 0]
            }
        })
        
        # Add all stations as features
        for feature in azure_data['features']:
            feature['properties'].update({
                "setup_cost": 5000.0,
                "monthly_cost": 1000.0,
                "cost_per_minute": 1.0,
                "cost_per_pass": 10.0,
                "per_satellite_license_cost": 1000.0,
                "antennas": 1
            })
            provider_feature["features"].append(feature)
        
        # Load the complete provider with all its stations
        provider = GroundStationProvider.load_geojson(provider_feature)
        optimizer.add_provider(provider)

    # Load satellites from TLE file
    satellites = read_tle_file('src/examples/data/celestrak_tles.txt')
    # Just use the first satellite for testing
    optimizer.add_satellite(satellites[0])

    # Compute contacts between satellites and ground stations
    optimizer.compute_contacts()
    
    # After computing contacts but before solving...
    
    # Add constraints
    from examples.gsopt.milp_constraints import MinConstellationDataDownlinkConstraint
    
    # Require at least 1 GB of data per day
    min_data_constraint = MinConstellationDataDownlinkConstraint(
        value=1e4,  # 1 GB in bits
        period=86400.0,  # One day in seconds
        step=360.0  # Check every hour
    )
    optimizer.add_constraint(min_data_constraint)
    
    # Set objective and solve
    optimizer.set_objective(MinCostObjective())
    optimizer.solve()
    
    print(optimizer)

    # After solving...
    solution = optimizer.get_solution()
    
    print("\nOptimization Results:")
    print(f"Solver Status: {solution['solver_status']}")
    print(f"Objective Value: {solution['objective_value']}")
    
    print("\nSelected Providers:")
    for provider in solution['selected_providers']:
        print(f"- {provider}")
    
    print("\nSelected Stations:")
    for station in solution['selected_stations']:
        print(f"- {station['name']} ({station['provider']})")
    
    print("\nData Downlink Statistics:")
    print(f"Total Data Downlinked: {solution['statistics']['data_downlinked']['total_GB']:.2f} GB")
    
    print("\nBy Satellite:")
    for sat_id, data in solution['statistics']['data_downlinked']['by_satellite']['daily_avg_GB'].items():
        print(f"- Satellite {sat_id}: {data:.2f} GB/day")
    
    print("\nCosts:")
    print(f"Total Cost: ${solution['statistics']['costs']['total']:.2f}")
    print(f"Fixed Cost: ${solution['statistics']['costs']['fixed']:.2f}")
    print(f"Operational Cost: ${solution['statistics']['costs']['operational']:.2f}")
    print(f"Monthly Operational Cost: ${solution['statistics']['costs']['monthly_operational']:.2f}")