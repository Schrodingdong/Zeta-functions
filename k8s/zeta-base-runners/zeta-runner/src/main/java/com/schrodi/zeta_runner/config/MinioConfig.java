package com.schrodi.zeta_runner.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties("object-storage")
public class MinioConfig {
    private String endpoint;
    private String username;
    private String password;
    private String bucket;

    public String getEndpoint() {
        return endpoint;
    }

    public String getPassword() {
        return password;
    }

    public String getUsername() {
        return username;
    }

    public String getBucket() {
        return bucket;
    }

    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public void setBucket(String bucket) {
        this.bucket = bucket;
    }
}
