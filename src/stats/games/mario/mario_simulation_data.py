import subprocess

# Playability computation for Super Mario Bros
java_path = "java"
jar_path = "src/stats/games/mario/Mario-AI-Framework/PerformSimulation.jar"
#temp_level_path = "temp_level.txt"
#temp_output_path = "temp_output.txt"
#temp_error_path = "temp_stderr.txt"
ram_limit = "-Xmx512m"
visuals = "False"
max_simulations = "10"

def simulation_data(level_file):
    #print("Performing simulation with level " + level_file)

    arguments = [ram_limit, "-jar", jar_path, level_file, max_simulations]

    try:
        result = subprocess.run([java_path] + arguments, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Unable to compute playability: {e.stderr}")
        return False, []#, []
    
    lines = output.splitlines()

    #print("Number of simulations performed: ", lines[1])
    
    if float(lines[0]) == 0.0:
        return False, []#, []
    
    actions = []
    for action in lines[2].split(","):
        actions.append(action)

    '''locations = []
    numbers = lines[2].split(",")
    for i in range(0, len(numbers), 2):
        locations.append((numbers[i], numbers[i+1]))'''

    return True, actions#, locations
