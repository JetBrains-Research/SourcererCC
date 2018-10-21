package com.mondego.models;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.lang.reflect.InvocationTargetException;
import java.util.concurrent.*;

public class ThreadedChannel<E> {

    private ExecutorService executor;
    private Class<? extends Runnable> workerType;
    private Semaphore semaphore;
    private static final Logger logger = LogManager
            .getLogger(ThreadedChannel.class);

    public ThreadedChannel(int nThreads, Class<? extends Runnable> clazz) {
        this.executor = Executors.newFixedThreadPool(nThreads);
        this.workerType = clazz;
        this.semaphore = new Semaphore(nThreads + 2);
    }

    public void send(E e) throws InstantiationException, IllegalAccessException,
            IllegalArgumentException, InvocationTargetException,
            NoSuchMethodException, SecurityException {
        final Runnable runnable = this.workerType.getDeclaredConstructor(e.getClass()).newInstance(e);
        try {
            semaphore.acquire();
        } catch (InterruptedException ex) {
            logger.error("Caught interrupted exception " + ex);
        }

        try {
            executor.execute(() -> {
                try {
                    runnable.run();
                } finally {
                    semaphore.release();
                }
            });
        } catch (RejectedExecutionException ex) {
            semaphore.release();
        }
    }

    public void shutdown() {
        this.executor.shutdown();
        try {
            this.executor.awaitTermination(Long.MAX_VALUE, TimeUnit.DAYS);
        } catch (InterruptedException e) {
            e.printStackTrace();
            logger.error("inside catch, shutdown");
        }
    }
}
