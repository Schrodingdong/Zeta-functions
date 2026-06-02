package com.schrodi.zeta_runner.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties("app.object-storage")
public class MinioConfig {
    private String serviceUrl;
    private String username;
    private String password;
    private String bucket;

    public String getServiceUrl() {
        return serviceUrl;
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

    public void setServiceUrl(String serviceUrl) {
        this.serviceUrl = serviceUrl;
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
