package com.mondego.models;

import com.mondego.indexbased.SearchManager;
import com.mondego.utility.Util;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.lang.reflect.InvocationTargetException;
import java.util.NoSuchElementException;
import java.util.Scanner;

public class CloneValidator implements IListener, Runnable {
    private CandidatePair candidatePair;
    private static final Logger logger = LogManager.getLogger(CloneValidator.class);

    public CloneValidator(CandidatePair candidatePair) {
        this.candidatePair = candidatePair;
    }

    @Override
    public void run() {
        try {
            this.validate(this.candidatePair);
        } catch (NoSuchElementException
                | InstantiationException
                | IllegalArgumentException
                | IllegalAccessException
                | SecurityException
                | InvocationTargetException
                | NoSuchMethodException e) {
            e.printStackTrace();
        }
    }

    private void validate(CandidatePair candidatePair)
            throws InstantiationException, IllegalAccessException, IllegalArgumentException,
            InvocationTargetException, NoSuchMethodException, SecurityException {
        /*
         * System.out.println(SearchManager.NODE_PREFIX + "validating, " +
         * candidatePair.candidateId + "query: " +
         * candidatePair.queryBlock.getFunctionId() + "," +
         * candidatePair.queryBlock.getId());
         */

        // long start_time = System.currentTimeMillis();
        long startTime = System.nanoTime();
        if (candidatePair.candidateTokens != null && candidatePair.candidateTokens.trim().length() > 0) {
            int similarity = this.updateSimilarity(candidatePair.queryBlock, candidatePair.candidateTokens,
                    candidatePair.computedThreshold, candidatePair.candidateSize, candidatePair.simInfo);
            if (similarity > 0) {
                com.mondego.models.ClonePair cp = new ClonePair(candidatePair.queryBlock.getFunctionId(), candidatePair.queryBlock.getId(),
                        candidatePair.functionIdCandidate, candidatePair.candidateId);

                /*
                 * long end_time = System.currentTimeMillis(); Duration
                 * duration; try { duration =
                 * DatatypeFactory.newInstance().newDuration( end_time -
                 * start_time); System.out.printf(SearchManager.NODE_PREFIX +
                 * ", validated: " + candidatePair.candidateId + "query: " +
                 * candidatePair.queryBlock.getFunctionId() + "," +
                 * candidatePair.queryBlock.getId() +
                 * " time taken: %02dh:%02dm:%02ds", duration.getDays() 24 +
                 * duration.getHours(), duration.getMinutes(),
                 * duration.getSeconds()); start_time = end_time;
                 * logger.debug(); } catch (DatatypeConfigurationException
                 * e) { e.printStackTrace(); }
                 */
                long estimatedTime = System.nanoTime() - startTime;
                logger.debug(SearchManager.NODE_PREFIX + " CloneValidator, QueryBlock " + candidatePair + " in " + estimatedTime / 1000 + " micros");
                SearchManager.reportCloneQueue.send(cp);
            }
            /*
             * candidatePair.queryBlock = null; candidatePair.simInfo = null;
             * candidatePair = null;
             */

        } else {
            logger.debug("tokens not found for document");
        }
    }

    private int updateSimilarity(QueryBlock queryBlock, String tokens, int computedThreshold, int candidateSize,
                                 CandidateSimInfo simInfo) {
        int tokensSeenInCandidate = 0;
        int similarity = simInfo.similarity;
        try (Scanner scanner = new Scanner(tokens)) {
            scanner.useDelimiter("::");
            String tokenfreqFrame;
            String[] tokenFreqInfo;
            TokenInfo tokenInfo;
            boolean matchFound;
            int candidatesTokenFreq;
            while (scanner.hasNext()) {
                tokenfreqFrame = scanner.next();
                tokenFreqInfo = tokenfreqFrame.split(":");
                if (Util.isSatisfyPosFilter(similarity, queryBlock.getSize(), simInfo.queryMatchPosition, candidateSize,
                        simInfo.candidateMatchPosition, computedThreshold)) {
                    // System.out.println("sim: "+ similarity);
                    candidatesTokenFreq = Integer.parseInt(tokenFreqInfo[1]);
                    tokensSeenInCandidate += candidatesTokenFreq;
                    if (tokensSeenInCandidate > simInfo.candidateMatchPosition) {
                        matchFound = false;
                        if (simInfo.queryMatchPosition < queryBlock.getPrefixMapSize()) {
                            // check in prefix
                            if (queryBlock.getPrefixMap().containsKey(tokenFreqInfo[0])) {
                                matchFound = true;
                                tokenInfo = queryBlock.getPrefixMap().get(tokenFreqInfo[0]);
                                similarity = updateSimilarityHelper(simInfo, tokenInfo, similarity,
                                        candidatesTokenFreq);
                            }
                        }
                        // check in suffix
                        if (!matchFound && queryBlock.getSuffixMap().containsKey(tokenFreqInfo[0])) {
                            tokenInfo = queryBlock.getSuffixMap().get(tokenFreqInfo[0]);
                            similarity = updateSimilarityHelper(simInfo, tokenInfo, similarity, candidatesTokenFreq);
                        }
                        if (similarity >= computedThreshold) {
                            return similarity;
                        }
                    }
                } else {
                    break;
                }
            }

        } catch (ArrayIndexOutOfBoundsException | NumberFormatException e) {
            logger.error("possible error in the format. tokens: " + tokens);
        }
        return -1;
    }

    private int updateSimilarityHelper(CandidateSimInfo simInfo, TokenInfo tokenInfo, int similarity,
                                       int candidatesTokenFreq) {
        simInfo.queryMatchPosition = tokenInfo.getPosition();
        similarity += Math.min(tokenInfo.getFrequency(), candidatesTokenFreq);
        // System.out.println("similarity: "+ similarity);
        return similarity;
    }
}
