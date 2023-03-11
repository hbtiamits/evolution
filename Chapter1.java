package com.learnjava.objectcreation;

import java.util.logging.Level;
import java.util.logging.Logger;

public class Chapter1 {
    private static Logger logger = Logger.getLogger("Chapter1");

    public static void main(String[] args) {
        logger.log(Level.INFO, "Test Programs on object creation...");
        Chapter1 ch1 = new Chapter1();
        ch1.instantiateNonInstantiableClass();
    }

    private void instantiateNonInstantiableClass(){
        //error: NonInstantiableClass() has private access in NonInstantiableClass
        // NonInstantiableClass nic = new NonInstantiableClass();
    }
}
