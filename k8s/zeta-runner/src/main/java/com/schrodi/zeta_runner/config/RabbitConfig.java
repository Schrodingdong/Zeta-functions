package com.schrodi.zeta_runner.config;

import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties("spring.rabbitmq")
public class RabbitConfig {
    @Value("${spring.rabbitmq.queues.deployment}")
    private String deploymentQueue;
    @Value("${spring.rabbitmq.queues.delete}")
    private String deleteQueue;

    @Bean
    public Queue zetaDeploymentQueue() {
        return QueueBuilder.durable(deploymentQueue).build();
    }

    @Bean
    public Queue zetaDeleteQueue() {
        return QueueBuilder.durable(deleteQueue).build();
    }
}