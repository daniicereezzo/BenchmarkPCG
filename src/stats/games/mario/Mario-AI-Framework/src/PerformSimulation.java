import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;

import engine.core.MarioGame;
import engine.core.MarioResult;

public class PerformSimulation {
    public static void main(String[] args) throws IOException {
        if(args.length < 1) {
            System.out.println("Usage: java PerformSimulation <level_path> <max_simulations>");
            System.exit(0);
        }

        String levelPath = args[0];
        String level = getLevel(levelPath);

        int maxSimulations = Integer.parseInt(args[1]);

        ArrayList<Integer> marioActions = new ArrayList<>();
        boolean isPlayable = false;
        int count;

        for(count = 0; count < maxSimulations && !isPlayable; count++) {
            MarioGame game = new MarioGame();
            MarioResult result = game.runGame(new agents.robinBaumgarten.Agent(), level, 20, 0, false);
            //printResults(result);

            isPlayable = result.getCompletionPercentage() >= 1;

            if(isPlayable){
                marioActions = result.getMarioActions();
            }
        }

        System.out.println(isPlayable ? "1" : "0");
        System.out.println(count);

        if (marioActions.size() > 0) {
            System.out.print(marioActions.get(0));
            for(int i = 1; i < marioActions.size(); i++) {
                System.out.print("," + marioActions.get(i));
            }
        }
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
}
