package com.mondego.models;

import com.mondego.indexbased.SearchManager;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.lang.reflect.InvocationTargetException;

public class QueryFileProcessor implements ITokensFileProcessor {
    private static final Logger logger = LogManager.getLogger(QueryFileProcessor.class);

    public QueryFileProcessor() {
    }

    @Override
    public void processLine(String line) {
        try {
            SearchManager.queryLineQueue.send(line);
        } catch (InstantiationException
                | IllegalAccessException
                | NoSuchMethodException
                | InvocationTargetException e) {
            e.printStackTrace();
        } catch (IllegalArgumentException e) {
            logger.error(e.getMessage()
                    + " skiping this query block, illegal args: "
                    + line.substring(0, 40));
            e.printStackTrace();
        }
    }

}
