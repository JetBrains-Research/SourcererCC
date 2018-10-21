package com.mondego.indexbased;

import org.apache.lucene.index.AtomicReaderContext;
import org.apache.lucene.search.Collector;
import org.apache.lucene.search.Scorer;

import java.util.ArrayList;
import java.util.List;

/**
 * @author vaibhavsaini
 */
public class CustomCollectorFwdIndex extends Collector {
    private List<Integer> blocks;
    private int docBase;

    public CustomCollectorFwdIndex() {
        this.blocks = new ArrayList<>();
    }

    @Override
    public boolean acceptsDocsOutOfOrder() {
        return true;
    }

    @Override
    public void collect(int doc) {
        Integer docId = doc + docBase;
        this.blocks.add(docId);
    }

    @Override
    public void setNextReader(AtomicReaderContext context) {
        this.docBase = context.docBase;
    }

    @Override
    public void setScorer(Scorer arg0) {
        // todo:
        // throw new UnsupportedOperationException("Operation not implemented");
    }

    /**
     * @return the blocks
     */
    public List<Integer> getBlocks() {
        return blocks;
    }

    /**
     * @param blocks the blocks to set
     */
    public void setBlocks(List<Integer> blocks) {
        this.blocks = blocks;
    }

}
