package com.schrodi.zetaapiserver.config;

import org.springframework.amqp.core.Queue;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties("spring.rabbitmq")
public class RabbitConfig {
    private String queue;

    @Bean
    public Queue zetaQueue() {
        return new Queue(queue, true);
    }

    public void setQueue(String queue) {
        this.queue = queue;
    }
}
