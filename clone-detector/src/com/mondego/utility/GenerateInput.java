package com.mondego.utility;

import com.mondego.models.Bag;
import com.mondego.noindex.CloneHelper;
import com.mondego.noindex.CloneTestHelper;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.util.Set;

/**
 * @author vaibhavsaini
 */
public class GenerateInput {
    public static void main(String[] args) {
        Set<Bag> setA = CloneTestHelper.getTestSet(1, 11);
        Set<Bag> setB = CloneTestHelper.getTestSet(11, 21);
        Writer projectAWriter = null;
        Writer projectBWriter = null;
        CloneHelper cloneHelper = new CloneHelper();
        try {
            File f = new File("projectA.txt");
            if (f.delete()) {
                System.out.println("deleted existing projectA.txt");
            }
            f = new File("projectB.txt");
            if (f.delete()) {
                System.out.println("deleted existing projectB.txt");
            }
            projectAWriter = Util.openFile("projectA.txt", false);
            Util.writeToFile(projectAWriter, cloneHelper.stringify(setA), true);
            projectBWriter = Util.openFile("projectB.txt", false);
            Util.writeToFile(projectBWriter, cloneHelper.stringify(setB), true);
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            try {
                Util.closeOutputFile(projectBWriter);
            } catch (Exception e) {
                System.err.println(e.getMessage());
            }
            try {
                Util.closeOutputFile(projectAWriter);
            } catch (Exception e) {
                System.err.println(e.getMessage());
            }
        }
    }

}
