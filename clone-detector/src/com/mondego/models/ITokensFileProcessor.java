package com.mondego.models;

import java.text.ParseException;

public interface ITokensFileProcessor {
    void processLine(String line) throws ParseException;
}
