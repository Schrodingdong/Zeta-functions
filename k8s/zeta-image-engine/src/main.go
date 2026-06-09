package main

import (
	"archive/zip"
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/gin-gonic/gin"

	"github.com/moby/go-archive"
	"github.com/moby/moby/client"
)

func main() {
	router := gin.Default()
	router.MaxMultipartMemory = 10 << 20 // 8 MiB

	// Init vars
	REGISTRY_URL := os.Getenv("REGISTRY_URL")
	IMAGE_VERSION := os.Getenv("IMAGE_VERSION")

	router.POST("/build", func(c *gin.Context) {
		// Get multipart data
		zetaName := c.Request.FormValue("name")
		file, err := c.FormFile("file")
		if err != nil {
			panic(err)
		}
		fmt.Printf("zeta name: %s\n", zetaName)
		fmt.Printf("file name: %s\n", file.Filename)

		// init tmp dir
		tmpDir, err := os.MkdirTemp("", fmt.Sprintf("zeta-%s-", zetaName))
		fmt.Println("Initialized tmpDir: " + tmpDir)
		if err != nil {
			panic(err)
		}
		defer os.RemoveAll(tmpDir)

		// Create tmp file and write zip in it
		tmpZip := tmpDir + "/" + file.Filename
		err = c.SaveUploadedFile(file, tmpZip)
		if err != nil {
			panic(err)
		}

		// Unzip the file
		tmpExtractedZipDir, err := os.MkdirTemp(tmpDir, fmt.Sprintf("zeta-%s-", zetaName))
		fmt.Println("Initialized tmpZipDir: " + tmpExtractedZipDir)
		if err != nil {
			panic(err)
		}
		err = unzipArchive(tmpZip, tmpExtractedZipDir)
		if err != nil {
			panic(err)
		}

		// init client ----------------
		fmt.Println("> Init client")
		apiClient, err := client.New(client.FromEnv)
		if err != nil {
			panic(err)
		}
		defer apiClient.Close()

		// Build the image ------------
		image := REGISTRY_URL + "/" + zetaName + ":" + IMAGE_VERSION
		tarBuildContext, err := archive.TarWithOptions(tmpExtractedZipDir, &archive.TarOptions{})
		if err != nil {
			panic(err)
		}
		defer tarBuildContext.Close()
		fmt.Println("> Building image: ", image)
		buildRes, err := apiClient.ImageBuild(context.Background(), tarBuildContext, client.ImageBuildOptions{
			Tags: []string{image},
		})
		buf := new(strings.Builder)
		io.Copy(buf, buildRes.Body)
		fmt.Println(buf.String())
		defer buildRes.Body.Close()
		if err != nil {
			panic(err)
		}

		// Push the image ------------
		fmt.Println("> Pushing the image: ", image)
		res, err := apiClient.ImagePush(context.Background(), image, client.ImagePushOptions{})
		if err != nil {
			panic(err)
		}
		defer res.Close()
		for msg, err := range res.JSONMessages(context.Background()) {
			fmt.Println(msg)
			if err != nil {
				panic(err)
			}
		}
		res.Wait(context.Background())

		// Return --------------------
		c.JSON(200, gin.H{
			"image":       image,
			"registryUrl": REGISTRY_URL,
		})

		fmt.Println("----------------------------")
	})

	router.Run()
}

func unzipArchive(srcArchive string, destFolder string) error {
	// 1. Open the zip file reader
	zipReader, err := zip.OpenReader(srcArchive)
	if err != nil {
		return err
	}
	defer zipReader.Close()

	// Clean destination path
	destFolder = filepath.Clean(destFolder)

	// 2. Loop through each file in the archive
	for _, archivedFile := range zipReader.File {
		// Securely resolve the destination file path
		filePath := filepath.Join(destFolder, archivedFile.Name)

		// Security Check: Mitigate Zip Slip vulnerability
		if !strings.HasPrefix(filepath.Clean(filePath), destFolder) {
			return fmt.Errorf("illegal file path detected: %s", archivedFile.Name)
		}

		// 3. Handle directory entries
		if archivedFile.FileInfo().IsDir() {
			if err := os.MkdirAll(filePath, archivedFile.Mode()); err != nil {
				return err
			}
			continue
		}

		// 4. Handle file entries: create parent directories if missing
		if err := os.MkdirAll(filepath.Dir(filePath), 0755); err != nil {
			return err
		}

		// Open the compressed content
		compressedFile, err := archivedFile.Open()
		if err != nil {
			return err
		}

		// Create the local target file
		targetFile, err := os.OpenFile(filePath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, archivedFile.Mode())
		if err != nil {
			compressedFile.Close()
			return err
		}

		// Stream content directly to disk
		_, err = io.Copy(targetFile, compressedFile)

		// Close files immediately to free descriptors during iteration
		targetFile.Close()
		compressedFile.Close()

		if err != nil {
			return err
		}
	}
	return nil
}
