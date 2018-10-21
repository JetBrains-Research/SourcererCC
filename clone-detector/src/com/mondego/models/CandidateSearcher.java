package com.mondego.models;

import com.mondego.indexbased.SearchManager;
import com.mondego.indexbased.TermSearcher;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.lang.reflect.InvocationTargetException;
import java.util.NoSuchElementException;

public class CandidateSearcher implements IListener, Runnable {
    private QueryBlock queryBlock;
    private static final Logger logger = LogManager.getLogger(CandidateSearcher.class);

    public CandidateSearcher(QueryBlock queryBlock) {
        this.queryBlock = queryBlock;
    }

    @Override
    public void run() {
        try {
            this.searchCandidates(queryBlock);
        } catch (NoSuchElementException
                | InstantiationException
                | IllegalArgumentException
                | IllegalAccessException
                | NoSuchMethodException
                | InvocationTargetException
                | SecurityException e) {
            e.printStackTrace();
        }
    }

    private void searchCandidates(QueryBlock queryBlock)
            throws InstantiationException, IllegalAccessException,
            IllegalArgumentException, InvocationTargetException, NoSuchMethodException, SecurityException {
        long startTime = System.nanoTime();
        int shard = queryBlock.getShardId();
        TermSearcher termSearcher = new TermSearcher(shard, queryBlock.getId());

        SearchManager.searcher.get(shard).search(queryBlock, termSearcher);

        QueryCandidates qc = new QueryCandidates();
        qc.queryBlock = queryBlock;
        qc.termSearcher = termSearcher;
        long estimatedTime = System.nanoTime() - startTime;
        logger.debug(SearchManager.NODE_PREFIX + " CandidateSearcher, QueryBlock " + queryBlock + " in shard " +
                shard + " in " + estimatedTime / 1000 + " micros");
        SearchManager.queryCandidatesQueue.send(qc);
    }

}
