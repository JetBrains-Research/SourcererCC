package com.mondego.indexbased;

import com.mondego.utility.Util;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class InputGen {
    private List<String> methodBlocks;
    private Writer queryBlockWriter;

    public InputGen() {
        this.methodBlocks = new ArrayList<>();
        try {
            this.queryBlockWriter = Util.openFile("input/query/genQueryFile.txt", false);
        } catch (IOException e) {
            System.out.println(e.getMessage());
            System.exit(1);
        }
    }

    private void genInputFile() {
        File datasetDir = new File(SearchManager.DATASET_DIR);
        if (datasetDir.isDirectory()) {
            System.out.println("Directory: " + datasetDir.getName());
            // populate methodsBlocksLIst
            for (File inputFile : datasetDir.listFiles()) {
                this.populateMethodBlocksList(inputFile);
            }
            System.out.println(this.methodBlocks.size());
            // create queryBlocksList
            this.createQueryFile();
            Util.closeOutputFile(queryBlockWriter);
        }
    }

    private void createQueryFile() {
        int min = 0;
        int max = this.methodBlocks.size();
        System.out.println(min + " : " + max);
        Random rand = new Random();
        for (int i = 0; i < 500; i++) {
            int randomNum = rand.nextInt((max - min) + 1) + min;
            System.out.println(randomNum);
            Util.writeToFile(this.queryBlockWriter,
                    this.methodBlocks.get(randomNum), true);
        }

    }

    private void populateMethodBlocksList(File inputFile) {
        BufferedReader br = null;
        System.out.println("file: " + inputFile.getName());
        try {
            br = new BufferedReader(new FileReader(inputFile));
            String line;
            while ((line = br.readLine()) != null && line.trim().length() > 0) {
                this.methodBlocks.add(line);
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            try {
                if (br != null) {
                    br.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static void main(String[] args) {
        InputGen inputGen = new InputGen();
        System.out.println("starting..");
        inputGen.genInputFile();
        System.out.println("done");
    }

}
