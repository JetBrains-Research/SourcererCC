package com.mondego.validation;

import com.mondego.postprocessing.ClonesBugsAssembler;
import com.mondego.utility.Util;

import java.io.IOException;
import java.io.Writer;
import java.util.Map;
import java.util.Set;

public class CloneBugPattern {
    private Writer outputWriter;
    /**
     * @param args
     */
    private ClonesBugsAssembler assembler;

    public CloneBugPattern() {
        super();
        this.assembler = new ClonesBugsAssembler();
    }

    public static void main(String[] args) {
        CloneBugPattern bugPattern = new CloneBugPattern();
        if (args.length > 0) {
            bugPattern.assembler.setProjectName(args[0]);
            String filename = "output/" + bugPattern.assembler.getProjectName()
                    + "-clones_validation.csv";
            System.out.println(filename);
            try {
                bugPattern.outputWriter = Util.openFile(filename, false);
                String bugInfoFile = "input/findbug/findbugs-" + bugPattern.assembler.getProjectName()
                        + ".csv"; //findbugs-cglib
                bugPattern.assembler.setBugInfoFile(bugInfoFile);
                bugPattern.assembler.process();
                bugPattern.createOutput();
            } catch (IOException e) {
                e.printStackTrace();
                System.out.println("error in file creation, exiting");
                System.exit(1);
            } finally {
                Util.closeOutputFile(bugPattern.outputWriter);
            }

        } else {
            System.out
                    .println("Please provide inputfile prefix, e.g. ANT,cocoon,hadoop.");
            System.exit(1);
        }
    }

    // 1)read clonesname.csv
    // 2) read methodbugdensity.csv
    // 3) for a method and it's clones, get row from methodbugdensity and put
    // that in outputfile
    // 4) enter a blank line

    private void createOutput() {
        Map<String, String> clonesNameMap = this.assembler.getClonesNameMap();
        Set<String> methods = clonesNameMap.keySet();
        boolean found;
        boolean ret;
        Util.writeToFile(this.outputWriter, "sep=" + Util.CSV_DELIMITER, true);
        for (String method : methods) {
            StringBuilder sb = new StringBuilder();
            String valueString = clonesNameMap.get(method);
            String[] values = valueString.split(Util.CSV_DELIMITER);
            String clones = values[0];
            String[] cv = clones.split("::");
            ret = this.appendBugInfo(method, sb);
            found = ret;
            for (String aCv : cv) {
                ret = this.appendBugInfo(aCv, sb);
                found = found || ret;
            }
            if (found) {
                Util.writeToFile(this.outputWriter, sb.toString(), true);
            }

        }
    }

    private boolean appendBugInfo(String method, StringBuilder sb) {
        Map<String, String> bugsInfoMap = this.assembler.getMethodListing();
        if (bugsInfoMap.containsKey(method)) {
            sb.append(method).append(Util.CSV_DELIMITER).append(bugsInfoMap.get(method)).append("\n");
            //Util.writeToFile(this.outputWriter, sb.toString(), true);
            return true;
        } else {
            sb.append(method).append("\n");
        }
        return false;
    }

}
