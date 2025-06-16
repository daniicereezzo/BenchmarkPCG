import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.io.FileWriter;

import engine.core.MarioGame;
import engine.core.MarioResult;

public class EvaluatePlayability_old {
    public static void main(String[] args) {
        if(args.length < 2) {
            System.out.println("Usage: java EvaluatePlayability <seed> <output_folder>");
            System.exit(0);
        }

        int seed = Integer.parseInt(args[0]);
        String outputFolder = args[1];

        // Set random seed
        Random random = new Random(seed);
    
        String generatorsFolder = "../Generators/";                                          // Folder where the generators are stored
        List<String> generatorsLevelsFolder = new ArrayList<>();
        //generatorsLevelsFolder.add("ProMP/new_levels");
        //generatorsLevelsFolder.add("GA2014/levels/levels_default");
        //generatorsLevelsFolder.add("GA2024/levels/levels_default");
        //generatorsLevelsFolder.add("OriginalMarioGAN/levels/levels_default_gan");
        //generatorsLevelsFolder.add("OriginalMarioGAN/levels/levels_default_mariogan");
        //generatorsLevelsFolder.add("CorrectedMarioGAN/levels_v1/levels_default_gan");
        //generatorsLevelsFolder.add("CorrectedMarioGAN/levels_v1/levels_default_mariogan");
        //generatorsLevelsFolder.add("CorrectedMarioGAN/levels_v2/levels_default_gan");
        //generatorsLevelsFolder.add("CorrectedMarioGAN/levels_v2/levels_default_mariogan");
        //generatorsLevelsFolder.add("MarioGPT/new_levels/levels_temperature_2.0");
        //generatorsLevelsFolder.add("MarioGPT/new_levels/levels_temperature_2.4");

        List<String> outputFiles = new ArrayList<>();
        //outputFiles.add("Playability_ProMP.csv");
        //outputFiles.add("Playability_GA2014.csv");
        //outputFiles.add("Playability_GA2024.csv");
        //outputFiles.add("Playability_OriginalGAN.csv");
        //outputFiles.add("Playability_OriginalMarioGAN.csv");
        //outputFiles.add("Playability_CorrectedGAN_v1.csv");
        //outputFiles.add("Playability_CorrectedGAN_v2.csv");
        //outputFiles.add("Playability_CorrectedMarioGAN_v1.csv");
        //outputFiles.add("Playability_CorrectedMarioGAN_v2.csv");
        //outputFiles.add("Playability_MarioGPT_2.0.csv");
        //outputFiles.add("Playability_MarioGPT_2.4.csv");

        // Experiment 2 evaluation
        String parent_path = "GA2014/levels";
        try {
            Files.walk(Paths.get(generatorsFolder + parent_path)).forEach(filePath -> {
                if (Files.isDirectory(filePath) && !filePath.getFileName().toString().equals("levels")) {
                    System.out.println(filePath.getFileName().toString());
                    generatorsLevelsFolder.add(parent_path + "/" + filePath.getFileName().toString());
                    outputFiles.add("Playability_" + filePath.getFileName().toString() + ".csv");
                }
            });
        } catch (IOException e) {
            e.printStackTrace();
        }

        for(String generatorLevelsFolder : generatorsLevelsFolder) {
            // Get all levels from the generator
            List<String> levels_files = new ArrayList<>();
            try {
                System.out.println("Reading levels from: " + generatorsFolder + generatorLevelsFolder);
                Files.walk(Paths.get(generatorsFolder + generatorLevelsFolder)).forEach(filePath -> {
                    if (Files.isRegularFile(filePath)) {
                        levels_files.add(filePath.toString());
                    }
                });
            } catch (IOException e) {
                e.printStackTrace();
                System.exit(1);
            }

            List<Integer> results = new ArrayList<>();

            for(String level_file : levels_files) {
                System.out.println("Evaluating level: " + level_file);
                
                String level = from_vglc_to_mario_ai(getLevel(level_file), random);
                boolean playable = IsPlayable(level);

                results.add(playable ? 1 : 0);
            }
            
            try {
                FileWriter writer = new FileWriter(outputFolder + outputFiles.get(generatorsLevelsFolder.indexOf(generatorLevelsFolder)));
                writer.write("Level,Playable\n");
                for(int i = 0; i < levels_files.size(); i++) {
                    writer.write(levels_files.get(i) + "," + results.get(i) + "\n");
                }
                writer.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static boolean IsPlayable(String level) {
        for(int i = 0; i < 10; i++) {
            MarioGame game = new MarioGame();
            MarioResult result = game.runGame(new agents.robinBaumgarten.Agent(), level, 20, 0, false);
            //printResults(result);

            if(result.getCompletionPercentage() >= 1) {
                return true;
            }
        }

        return false;
    }

    public static void printResults(MarioResult result) {
        System.out.println("****************************************************************");
        System.out.println("Game Status: " + result.getGameStatus().toString() +
                " Percentage Completion: " + result.getCompletionPercentage());
        System.out.println("Lives: " + result.getCurrentLives() + " Coins: " + result.getCurrentCoins() +
                " Remaining Time: " + (int) Math.ceil(result.getRemainingTime() / 1000f));
        System.out.println("Mario State: " + result.getMarioMode() +
                " (Mushrooms: " + result.getNumCollectedMushrooms() + " Fire Flowers: " + result.getNumCollectedFireflower() + ")");
        System.out.println("Total Kills: " + result.getKillsTotal() + " (Stomps: " + result.getKillsByStomp() +
                " Fireballs: " + result.getKillsByFire() + " Shells: " + result.getKillsByShell() +
                " Falls: " + result.getKillsByFall() + ")");
        System.out.println("Bricks: " + result.getNumDestroyedBricks() + " Jumps: " + result.getNumJumps() +
                " Max X Jump: " + result.getMaxXJump() + " Max Air Time: " + result.getMaxJumpAirTime());
        System.out.println("****************************************************************");
    }

    public static String getLevel(String filepath) {
        String content = "";
        try {
            content = new String(Files.readAllBytes(Paths.get(filepath)));
            //System.out.println(content);
        } catch (IOException e) {
            System.out.println("Error reading file: " + filepath);
        }
        return content;
    }

    public static String from_vglc_to_mario_ai(String level, Random random) {
        for(int i = 0; i < level.length(); i++) {
            if(level.charAt(i) == '<' || level.charAt(i) == '>' || level.charAt(i) == '[' || level.charAt(i) == ']') {
                level = level.substring(0, i) + 't' + level.substring(i + 1);
            }
            else if(level.charAt(i) == 'b' || level.charAt(i) == 'B') {
                level = level.substring(0, i) + '*' + level.substring(i + 1);
            }
            else if(level.charAt(i) == '?') {
                double r = random.nextDouble();
                if(r < 0.2){
                    level = level.substring(0, i) + 'C' + level.substring(i + 1);
                }
                else if(r < 0.4){
                    level = level.substring(0, i) + 'L' + level.substring(i + 1);
                }
                else if(r < 0.6){
                    level = level.substring(0, i) + 'U' + level.substring(i + 1);
                }
                else if(r < 0.8){
                    level = level.substring(0, i) + '@' + level.substring(i + 1);
                }
                else{
                    level = level.substring(0, i) + '!' + level.substring(i + 1);
                }
            }
            else if(level.charAt(i) == 'Q') {
                level = level.substring(0, i) + 'D' + level.substring(i + 1);
            }
            else if(level.charAt(i) == 'E') {
                level = level.substring(0, i) + 'g' + level.substring(i + 1);
            }
            
        }

        //System.out.println(level);
        return level;
    }
}
