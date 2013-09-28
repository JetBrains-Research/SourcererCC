/**
 * 
 */
package utility;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Random;

/**
 * @author vaibhavsaini
 * 
 */
public class Util {
    static Random rand = new Random(3);

    /**
     * generates a random integer
     * @return
     */
    public static int getRandomNumber(int max , int min) {
        return rand.nextInt((max - min) + 1) + min;
    }

    /**
     * writes the given text to a file pointed by pWriter
     * 
     * @param pWriter
     *            handle to printWriter to write to a file
     * @param text
     *            text to be written in the file
     * @param isNewline
     *            whether to start from a newline or not
     */
    public static void writeToFile(PrintWriter pWriter, final String text,
            final boolean isNewline) {
        if (isNewline) {
            pWriter.println(text);
        } else {
            pWriter.print(text);
        }
    }

    /**
     * opens the outputfile for reporting clones
     * 
     * @param filename
     * @throws IOException
     * @return PrintWriter
     */
    public static PrintWriter openFileToWrite(String filename)
            throws IOException {
        try {
            PrintWriter pWriter = new PrintWriter(new BufferedWriter(
                    new FileWriter(filename, true)));
            return pWriter;

        } catch (IOException e) {
            // IO exception caught
            System.err.println(e.getMessage());
            throw e;
        }
    }
    
    /**
     * closes the outputfile
     */
    public static void closeOutputFile(PrintWriter pWriter) {
        pWriter.close();
    }
}
