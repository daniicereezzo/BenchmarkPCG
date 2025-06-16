package io;

public class SaveLevel {
    public static void saveLevelStringToFile(String level, String fileName) {
        try {
            java.io.PrintWriter out = new java.io.PrintWriter(fileName);
            String[] lines = level.split("\\r?\\n");
            for (String line : lines) {
                out.println(line);
            }
            out.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
