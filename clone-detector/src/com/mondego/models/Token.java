package com.mondego.models;

/**
 * Class holding token as a String and it's id
 */
public class Token {
    /**
    * Value of token, e.g. 'for'
    */
    private String value;
    /**
    * Unique id of a token
    */
    private int id = 0;

    /**
    * Token constructor by token value
    */
    public Token(String value) {
        super();
        this.value = value;
    }

    /**
     * @return the id of a token
     */
    public int getId() {
        return id;
    }

    /**
     * @param id the id to set
     */
    public void setId(int id) {
        this.id = id;
    }

    /**
     * @see java.lang.Object#hashCode()
     */
    @Override
    public int hashCode() {
        return value.hashCode();
    }

    /**
     * @see java.lang.Object#equals(java.lang.Object)
     */
    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (!(obj instanceof Token)) {
            return false;
        }
        Token other = (Token) obj;
        return (value != null && value.equals(other.value) || value == null && other.value == null);
    }

    /**
     * @see java.lang.Object#toString()
     */
    @Override
    public String toString() {
        return value;
    }

    /**
     * @return the value of a token
     */
    public String getValue() {
        return value;
    }

    /**
     * @param value the value to set to a token
     */
    public void setValue(String value) {
        this.value = value;
    }
}
