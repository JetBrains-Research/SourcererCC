package models;

import indexbased.DocumentMaker;
import indexbased.SearchManager;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.List;
import java.util.NoSuchElementException;

import org.apache.lucene.document.Document;

public class InvertedIndexCreator implements IListener, Runnable {
    private DocumentMaker documentMaker;
    private Document document;
    private Bag bag;

    public InvertedIndexCreator(Bag bag) {
        super();
        this.documentMaker = new DocumentMaker();
        this.bag = bag;
    }

    @Override
    public void run() {
        try {
            /*
             * System.out.println(SearchManager.NODE_PREFIX +
             * ", size of bagsToInvertedIndexQueue " +
             * SearchManager.bagsToInvertedIndexQueue.size());
             */
            this.index(this.bag);
        } catch (NoSuchElementException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (InstantiationException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (IllegalAccessException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (InvocationTargetException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (NoSuchMethodException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (SecurityException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }

    }

    private void index(Bag bag) throws InterruptedException, InstantiationException, IllegalAccessException,
            IllegalArgumentException, InvocationTargetException, NoSuchMethodException, SecurityException {
        List<Shard> shards = SearchManager.getShardIdsForBag(bag);
        this.document = this.documentMaker.prepareDocument(bag);
        for (Shard shard : shards) {
            try {
                System.out.println(shard);
                shard.getInvertedIndexWriter().addDocument(this.document);
            } catch (IOException e) {
                System.out.println(SearchManager.NODE_PREFIX + ": error in indexing bag, " + bag);
                e.printStackTrace();
            }
        }
        SearchManager.bagsToForwardIndexQueue.send(bag);
    }

    public DocumentMaker getIndexer() {
        return documentMaker;
    }
}