package com.schrodi.zetaapiserver.config;

import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.support.converter.SimpleMessageConverter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
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

    @Bean
    public SimpleMessageConverter messageConverter() {
        SimpleMessageConverter converter = new SimpleMessageConverter();
        // Allow java.lang.Enum alongside your application packages
        converter.setAllowedListPatterns(List.of(
                "java.lang.*",
                "java.utils.*",
                "com.schrodi.zetaapiserver.*"
        ));
        return converter;
    }
}
