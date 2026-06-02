package com.schrodi.zetaapiserver.service;

import com.schrodi.zetaapiserver.config.MinioConfig;
import com.schrodi.zetaapiserver.dto.DeploymentTask;
import com.schrodi.zetaapiserver.dto.ZetaRequest;
import com.schrodi.zetaapiserver.dto.ZetaResponse;
import com.schrodi.zetaapiserver.exception.ZetaNotFoundException;
import com.schrodi.zetaapiserver.model.Zeta;
import com.schrodi.zetaapiserver.model.ZetaStatus;
import com.schrodi.zetaapiserver.repository.ZetaRepository;
import io.minio.MinioClient;
import io.minio.UploadObjectArgs;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;

@Service
public class ZetaService {
    private static final String PREFIX = "zeta-";
    private final MinioClient minioClient;
    private final MinioConfig minioConfig;
    private final ZetaRepository zetaRepository;
    private final WorkQueue workQueue;


    public ZetaService(ZetaRepository zetaRepository, MinioClient minioClient,  MinioConfig minioConfig, WorkQueue workQueue) {
        this.minioClient = minioClient;
        this.minioConfig = minioConfig;
        this.zetaRepository = zetaRepository;
        this.workQueue = workQueue;
    }

    public ZetaResponse getZeta(String id) {
        UUID uuid = UUID.fromString(id);
        Zeta zeta = zetaRepository.findById(uuid)
                .orElseThrow(() -> new ZetaNotFoundException(String.format("Zeta of id %s not found", id)));
        return new ZetaResponse(zeta.getZetaName(), zeta.getZetaStatus());
    }

    public ZetaResponse deployZeta(ZetaRequest zetaRequest) {
        // Save in DB
        Zeta zeta = new Zeta();
        zeta.setZetaStatus(ZetaStatus.PENDING);
        zeta.setZetaName(zetaRequest.name());

        zeta = zetaRepository.save(zeta);

        // Save the file in tmp
        Path tmpDir;
        Path tmpZipPath;
        try {
            tmpDir = Files.createTempDirectory(PREFIX + zetaRequest.name() + "_");
            tmpZipPath = Files.createTempFile(tmpDir, zetaRequest.name() + "_", ".zip");
            Files.write(tmpZipPath, zetaRequest.file().getBytes());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // Upload
        try {
            UploadObjectArgs uploadObjectArgs = UploadObjectArgs.builder()
                    .bucket(minioConfig.getBucket())
                    .object(zetaRequest.name() + ".zip")
                    .filename(tmpZipPath.toString())
                    .build();
            minioClient.uploadObject(uploadObjectArgs);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        // Update status to deploying
        zeta.setZetaStatus(ZetaStatus.DEPLOYING);
        zeta = zetaRepository.save(zeta);

        // send to workqueueu
        workQueue.send(new DeploymentTask(zeta.getZetaName()));

        return new ZetaResponse(zeta.getZetaName(), zeta.getZetaStatus());
    }
}
