package com.mondego.models;

import java.util.LinkedHashSet;

/**
 * Set of tokenFrequencies able to find similar token in get(TokenFrequency) method.
 */
public class Bag extends LinkedHashSet<TokenFrequency>  { 
    private static final long serialVersionUID = 1721183896451527542L;
    private long id;
    private int size = 0;
    private int comparisions = 0;
    private long functionId = -1;

    /**
    * @param bagId id of bag to set
    */
    public Bag(long bagId) {
        super();
        this.id = bagId;
    }

    public Bag() {
        super();
    }

    /**
    * Returns token similar to tokenFrequency and counts comparisons made
    *
    * @param tokenFrequency token to find(don't know why with frequency)
    * @return object of TokenFrequency class with same Token inside, null if not found
    */
    public TokenFrequency get(TokenFrequency tokenFrequency) {
        this.comparisions = 0;
        for (TokenFrequency tf : this) {
            this.comparisions += 1;
            if (tf.equals(tokenFrequency)) {
                return tf;
            }
        }
        return null;
    }

    /**
    * @return comparisons made during get(TokenFrequency)
    */
    public int getComparisions() {
        return comparisions;
    }

    /**
    * @return functionId of bag
    */
    public long getFunctionId() {
        return functionId;
    }

    /**
    * @param functionId to set to bag
    */
    public void setFunctionId(long functionId) {
        this.functionId = functionId;
    }

    /**
     * @return the id
     */
    public long getId() {
        return this.id;
    }

    /**
    * Counts and returns total number of tokens
    *
    * @return sum of all frequencies of all tokens
    */
    public int getSize() {
        if (this.size == 0) {
            for (TokenFrequency tf : this) {
                this.size += tf.getFrequency();
            }
        }
        return this.size;
    }

    public void setSize(int size){
        this.size = size;
    }

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = super.hashCode();
        result = prime * result + (int) (id ^ (id >>> 32));
        return result;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (!super.equals(obj) || getClass() != obj.getClass())
            return false;
        Bag other = (Bag) obj;
        return id == other.id;
    }

    /**
     * @see java.lang.Object#toString()
     */
    @Override
    public String toString() {
        return this.getFunctionId() + ":" + this.getId() + ":" + this.getSize();
    }
}
