package com.schrodi.zetaapiserver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class ZetaApiserverApplication {

    public static void main(String[] args) {
        SpringApplication.run(ZetaApiserverApplication.class, args);
    }

}
