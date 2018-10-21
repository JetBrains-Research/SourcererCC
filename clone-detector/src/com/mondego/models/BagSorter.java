package com.mondego.models;

import com.mondego.indexbased.SearchManager;
import com.mondego.utility.Util;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.lang.reflect.InvocationTargetException;
import java.util.NoSuchElementException;

public class BagSorter implements IListener, Runnable {
    private Bag bag;
    private static final Logger logger = LogManager.getLogger(BagSorter.class);

    public BagSorter(Bag bag) {
        this.bag = bag;
    }

    @Override
    public void run() {
        try {
            /*
             * System.out.println(SearchManager.NODE_PREFIX +
             * ", size of bagsToSortQueue " +
             * SearchManager.bagsToSortQueue.size());
             */
            this.sortBag(this.bag);
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

    private void sortBag(Bag bag) throws InstantiationException, IllegalAccessException,
            IllegalArgumentException, InvocationTargetException, NoSuchMethodException, SecurityException {
        long startTime = System.nanoTime();
        Util.sortBag(bag);
        long estimatedTime = System.nanoTime() - startTime;
        logger.info(SearchManager.NODE_PREFIX + " SB, Bag " + bag + " in " + estimatedTime / 1000 + " micros");
        SearchManager.bagsToInvertedIndexQueue.send(bag);
    }
}
