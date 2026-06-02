package com.schrodi.zeta_runner.utils;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class ZipUtils {
    public static void unzip(Path zipFile, Path destinationDir) throws IOException {
        Files.createDirectories(destinationDir);

        try (InputStream fis = Files.newInputStream(zipFile);
             ZipInputStream zis = new ZipInputStream(fis)) {

            ZipEntry entry;

            while ((entry = zis.getNextEntry()) != null) {
                Path targetPath = destinationDir.resolve(entry.getName()).normalize();

                // Prevent Zip Slip vulnerability
                if (!targetPath.startsWith(destinationDir)) {
                    throw new IOException("Invalid ZIP entry: " + entry.getName());
                }

                if (entry.isDirectory()) {
                    Files.createDirectories(targetPath);
                } else {
                    Files.createDirectories(targetPath.getParent());

                    try (OutputStream os = Files.newOutputStream(targetPath)) {
                        zis.transferTo(os);
                    }
                }

                zis.closeEntry();
            }
        }
    }
}
