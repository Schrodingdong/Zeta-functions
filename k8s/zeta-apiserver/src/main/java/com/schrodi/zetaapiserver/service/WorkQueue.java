package com.schrodi.zetaapiserver.service;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.schrodi.zetaapiserver.dto.DeploymentTask;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeoutException;

@Component
public class WorkQueue {
    private static final String QUEUE_NAME = "zeta-deployment";
    private final ConnectionFactory factory;
    private final ObjectMapper mapper;

    public WorkQueue(ConnectionFactory factory, ObjectMapper mapper) {
        this.factory = factory;
        this.mapper = mapper;
    }

    public void send(DeploymentTask task) {
        try (Connection connection = factory.newConnection();
             Channel channel = connection.createChannel()) {
            Map<String, Object> args = Map.of("x-queue-type", "quorum");
            channel.queueDeclare(QUEUE_NAME, true, false, false, args);

            String taskStr = mapper.writeValueAsString(task);
            channel.basicPublish("", QUEUE_NAME, null, taskStr.getBytes());
        } catch (IOException e) {
            throw new RuntimeException(e);
        } catch (TimeoutException e) {
            throw new RuntimeException(e);
        }
    }
}
