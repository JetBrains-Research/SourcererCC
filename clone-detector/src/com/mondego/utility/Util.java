package com.mondego.utility;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;
import com.mondego.indexbased.SearchManager;
import com.mondego.models.Bag;
import com.mondego.models.TokenFrequency;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.*;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.Map.Entry;

/**
 * @author vaibhavsaini
 */
public class Util {
    private static Random random = new Random(5);
    public static final String CSV_DELIMITER = "~";
    public static final String INDEX_DIR = SearchManager.ROOT_DIR + "index";
    public static final String INDEX_DIR_TEMP = SearchManager.ROOT_DIR
            + "index_temp";
    public static final String GTPM_DIR = SearchManager.ROOT_DIR + "gtpm";
    public static final String GLOBAL_WFM_DIR = SearchManager.ROOT_DIR + "wfm";
    public static final String FWD_INDEX_DIR = SearchManager.ROOT_DIR
            + "fwdindex";
    public static final String FWD_INDEX_DIR_TEMP = SearchManager.ROOT_DIR
            + "fwdindex_temp";
    public static final String GTPM_INDEX_DIR = SearchManager.ROOT_DIR
            + "gtpmindex";
    public static final String INDEX_DIR_NO_FILTER = SearchManager.ROOT_DIR
            + "index_nofilter";
    public static final String QUERY_FILE_NAME = "blocks.file";
    public static final String OUTPUT_BACKUP_DIR = SearchManager.ROOT_DIR
            + "backup_output";
    public static final String SEARCH_METADATA = SearchManager.ROOT_DIR
            + "search_metadata.txt";
    public static final String RUN_METADATA = SearchManager.ROOT_DIR
            + "run_metadata.scc";
    private static final Logger logger = LogManager.getLogger(Util.class);

    /**
     * generates a random integer
     */
    public static int getRandomNumber(int max, int min) {
        return random.nextInt((max - min) + 1) + min;
    }

    /**
     * writes the given text to a file pointed by pWriter
     *
     * @param pWriter   handle to printWriter to write to a file
     * @param text      text to be written in the file
     * @param isNewline whether to start from a newline or not
     */
    public static synchronized void writeToFile(Writer pWriter,
                                                final String text, final boolean isNewline) {
        if (isNewline) {
            try {
                pWriter.write(text + System.lineSeparator());
            } catch (IOException e) {
                e.printStackTrace();
            }
        } else {
            try {
                pWriter.write(text);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        try {
            pWriter.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    /**
     * opens the outputfile for reporting clones
     *
     * @return PrintWriter
     */
    public static Writer openFile(String filename, boolean append) throws IOException {
        try {
            return new BufferedWriter(
                    new OutputStreamWriter(
                            new FileOutputStream(filename, append),
                            StandardCharsets.UTF_8
                    )
            );

        } catch (IOException e) {
            System.err.println(e.getMessage());
            throw e;
        }
    }

    /**
     * closes the outputfile
     */
    public static void closeOutputFile(Writer pWriter) {
        if (null != pWriter) {
            try {
                pWriter.flush();
            } catch (IOException e) {
                e.printStackTrace();
            }
            try {
                pWriter.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }

    }

    public static boolean createDirs(String dirname) {
        File dir = new File(dirname);
        if (!dir.exists()) {
            logger.info("creating directory: " + dirname);
            return dir.mkdirs();
        } else {
            return true;
        }
    }

    public static boolean isSatisfyPosFilter(int similarity, int querySize,
                                             int termsSeenInQueryBlock, int candidateSize,
                                             int termsSeenInCandidate, int computedThreshold) {
        return computedThreshold <= similarity
                + Math.min(querySize - termsSeenInQueryBlock,
                candidateSize - termsSeenInCandidate);
    }

    public static void writeJsonStream(String filename, Map<String, Integer> gtpm) {
        Writer writer = null;
        try {
            writer = Util.openFile(filename, false);
            Gson gson = new GsonBuilder().create();
            String text = gson.toJson(gtpm);
            Util.writeToFile(writer, text, false);
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            try {
                writer.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static String debug_thread() {
        return "  Thread_id: " + Thread.currentThread().getId()
                + " Thread_name: " + Thread.currentThread().getName();
    }

    public static Map<String, Integer> readJsonStream(String filename) {
        Map<String, Integer> gtpm = new HashMap<>();
        try (FileInputStream fileInputStream = new FileInputStream(filename);
             InputStreamReader inputStreamReader = new InputStreamReader(fileInputStream, StandardCharsets.UTF_8);
             BufferedReader bufferedReader = new BufferedReader(inputStreamReader, 1024 * 1024 * 512)) {
            String line;
            while ((line = bufferedReader.readLine()) != null && line.trim().length() > 0) {
                Gson gson = new GsonBuilder().create();
                Type type = new TypeToken<Map<String, Integer>>() {
                }.getType();
                gtpm = gson.fromJson(line, type);
            }
        } catch (JsonSyntaxException | IOException e) {
            e.printStackTrace();
        }
        return gtpm;

    }

    public static <K, V> Map<K, V> lruCache(final int maxSize) {
        return Collections.synchronizedMap(
                new LinkedHashMap<>(maxSize * 4 / 3, 0.75f, true) {
                    @Override
                    protected boolean removeEldestEntry(
                            Map.Entry<K, V> eldest) {
                        return size() > maxSize;
                    }
                });
    }

    // This cache is shared by all threads that call sortBag
    private final static Map<String, Long> cache = lruCache(500000);

    public static void sortBag(final Bag bag) {
        List<TokenFrequency> bagAsList = new ArrayList<>(bag);
        logger.debug("bag to sort: " + bag);
        try {
            bagAsList.sort((tfFirst, tfSecond) -> {
                Long frequency1;
                Long frequency2;
                String k1 = tfFirst.getToken().getValue();
                String k2 = tfSecond.getToken().getValue();
                if (cache.containsKey(k1)) {
                    frequency1 = cache.get(k1);
                    if (null == frequency1) {
                        logger.warn("freq1 null from cache");
                        frequency1 = SearchManager.gtpmSearcher
                                .getFrequency(k1);
                        cache.put(k1, frequency1);
                    }
                } else {
                    frequency1 = SearchManager.gtpmSearcher
                            .getFrequency(k1);
                    cache.put(k1, frequency1);
                }
                if (cache.containsKey(k2)) {
                    frequency2 = cache.get(k2);
                    if (null == frequency2) {
                        logger.warn("freq2 null from cache");
                        frequency2 = SearchManager.gtpmSearcher
                                .getFrequency(k2);
                        cache.put(k2, frequency2);
                    }
                } else {
                    frequency2 = SearchManager.gtpmSearcher
                            .getFrequency(k2);
                    cache.put(k2, frequency2);
                }
                int result = frequency1.compareTo(frequency2);
                if (result == 0) {
                    return k1.compareTo(k2);
                } else {
                    return result;
                }
            });
            bag.clear();
            bag.addAll(bagAsList);
        } catch (NullPointerException e) {
            logger.error("NPE caught while sorting, ", e);
            SearchManager.FATAL_ERROR = true;
        }

    }

    /*
     * public static int getMinimumSimilarityThreshold(QueryBlock
     * queryBlock,float threshold) { return (int) Math.ceil((threshold *
     * queryBlock.getSize())/ (SearchManager.MUL_FACTOR*10)); } public static
     * int getMinimumSimilarityThreshold(Bag bag,float threshold) { return (int)
     * Math.ceil((threshold * bag.getSize())/ (SearchManager.MUL_FACTOR*10)); }
     */

    public static void writeMapToFile(String filename, Map<String, Long> map) {
        Writer writer = null;
        try {
            logger.debug("writing to : " + filename);
            writer = Util.openFile(filename, false);
            for (Entry<String, Long> entry : map.entrySet()) {
                String text = entry.getKey() + ":" + entry.getValue();
                Util.writeToFile(writer, text, true);
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            try {
                writer.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static Map<String, Long> readMapFromFile(String filename) {
        Map<String, Long> gtpm = new HashMap<>();
        try (FileInputStream fileInputStream = new FileInputStream(new File(filename));
             InputStreamReader inputStreamReader = new InputStreamReader(fileInputStream, StandardCharsets.UTF_8);
             BufferedReader bufferedReader = new BufferedReader(inputStreamReader)
        ) {
            logger.debug("here " + filename);
            logger.debug("file is " + filename);
            logger.debug(fileInputStream);
            logger.debug(inputStreamReader);
            logger.debug(bufferedReader);
            logger.debug("hi");
            String line;
            while ((line = bufferedReader.readLine()) != null && line.trim().length() > 0) {
                String[] keyValPair = line.split(":");
                gtpm.put(keyValPair[0], Long.parseLong(keyValPair[1]));
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return gtpm;

    }

    public static void populateProcessedWFMSet(String filename, Set<String> processedWFMset) {
        BufferedReader br;
        File f = new File(filename);
        logger.debug("file is " + f);
        FileInputStream fis;
        try {
            fis = new FileInputStream(f);
            logger.debug(fis);
            InputStreamReader ir = new InputStreamReader(fis, StandardCharsets.UTF_8);
            logger.debug(ir);
            br = new BufferedReader(ir);
            String line;
            while ((line = br.readLine()) != null && line.trim().length() > 0) {
                processedWFMset.add(line);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public static BufferedReader getReader(File queryFile)
            throws FileNotFoundException {
        BufferedReader br;
        br = new BufferedReader(new FileReader(queryFile));
        return br;
    }

    public static Writer openFile(File output, boolean append) throws IOException {
        return new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(output, append), StandardCharsets.UTF_8));
    }

    public static List<File> getAllFilesRecur(File root) {
        List<File> listToReturn = new ArrayList<>();
        for (File file : root.listFiles()) {
            if (file.isFile()) {
                listToReturn.add(file);
            } else if (file.isDirectory()) {
                listToReturn.addAll(getAllFilesRecur(file));
            }
        }
        return listToReturn;

    }
    /*
     * public static int getPrefixSize(QueryBlock queryBlock, float threshold) {
     * int prefixSize = (queryBlock.getSize() + 1) - computedThreshold;//
     * this.computePrefixSize(maxLength); return prefixSize; }
     */
    /*
     * public static int getPrefixSize(Bag bag, float threshold) { int
     * computedThreshold = getMinimumSimilarityThreshold(bag, threshold); int
     * prefixSize = (bag.getSize() + 1) - computedThreshold;//
     * this.computePrefixSize(maxLength); return prefixSize; }
     */
}
