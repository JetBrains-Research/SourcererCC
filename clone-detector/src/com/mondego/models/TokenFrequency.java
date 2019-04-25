package com.mondego.models;

/**
 * Class containing token and it's frequency
 */
public class TokenFrequency {
    /**
    * Frequency of a token
    */
    private int frequency;
    /**
    * Inner token
    */
    private Token token;
	
    /**
    * @return the frequency
    */
    public int getFrequency() {
        return frequency;
    }

    /**
     * @param frequency the frequency to set
     */
    public void setFrequency(int frequency) {
        this.frequency = frequency;
    }

    /**
     * @return the token
     */
    public Token getToken() {
        return token;
    }

    /**
     * @param token the token to set
     */
    public void setToken(Token token) {
        this.token = token;
    }

    /**
     * @see java.lang.Object#hashCode()
     */
    @Override
    public int hashCode() {
        return token.hashCode();
    }
    /**
     * @see java.lang.Object#equals(java.lang.Object)
     */
    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null  || !(obj instanceof TokenFrequency)) {
            return false;
        }
        TokenFrequency other = (TokenFrequency) obj;
        if (token == null && other.token != null) {
            return false;
        }
        return (token == null || token.getValue().equals(other.token.getValue()));
    }

    /**
     * @see java.lang.Object#toString()
     */
    @Override
    public String toString() {
        return String.format("TokenFrequency [frequency=%d, token=%s]", frequency, token.toString());
    }    
}
