package com.schrodi.zetaapiserver.config;

import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.errors.MinioException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class MinioInitializer implements CommandLineRunner {
    private static final Logger log = LoggerFactory.getLogger(MinioInitializer.class);
    private final MinioClient client;
    private final MinioConfig config;

    public MinioInitializer(MinioClient minioClient, MinioConfig minioConfig) {
        this.client = minioClient;
        this.config = minioConfig;
    }

    @Override
    public void run(String... args) throws MinioException {
        // Check if Bucket exists
        String bucket = config.getBucket();
        var bucketExistsArgs = BucketExistsArgs.builder()
                .bucket(bucket)
                .build();
        boolean found = client.bucketExists(bucketExistsArgs);
        if (!found) {
            log.info("Bucket {} does not exist. Creating the bucket...", bucket);
            var makeBucketArgs = MakeBucketArgs.builder()
                .bucket(bucket)
                .build();
            client.makeBucket(makeBucketArgs);
        }
    }
}
