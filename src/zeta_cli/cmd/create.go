package cmd

import (
	"bytes"
	"fmt"
	"io"
	"strings"

	"net/http"
	"os"

	"mime/multipart"

	"github.com/spf13/cobra"
	"github.com/zeta/constants"
)

func createHandler(cmd *cobra.Command, args []string) {
	zetaName := args[0]
	filepath := args[1]
	if len(zetaName) <= 1 {
		fmt.Printf("Zeta name '%v' should be at least 2 characters long.\n", zetaName)
		return
	}

	// read file
	file, err := os.Open(filepath)
	if err != nil {
		fmt.Printf("Unable to read content of file '%v'\n", filepath)
		return
	}
	defer file.Close()

	// Create the multipart/form-data to send
	var requestBody bytes.Buffer
	writer := multipart.NewWriter(&requestBody)
	part, err := writer.CreateFormFile("file", filepath)
	if err != nil {
		fmt.Printf("Unable to initialize multipart form file\n")
		fmt.Println(err)
		return
	}
	_, err = io.Copy(part, file)
	if err != nil {
		fmt.Printf("Unable to copy file content to multipart form file\n")
		fmt.Println(err)
		return
	}
	writer.Close() // sets the boundary

	// Forward the request
	path := "/zeta/create/" + zetaName
	resp, err := http.Post(constants.Url+path, writer.FormDataContentType(), &requestBody)
	if err != nil {
		fmt.Printf("Unable to communicate with docker-proxy\n")
		fmt.Println(err)
		return
	}

	statusCode := strings.Split(resp.Status, " ")[0]
	if statusCode != "201" {
		fmt.Printf("Error creating the zeta function\n")
		fmt.Printf("> status code: %v\n", resp.Status)
		body, err := io.ReadAll(resp.Body)
		if err == nil {
			fmt.Printf("> body: %v\n", body)
		}
		return
	}

	zetaUrl := constants.Url + "/zeta/run/" + zetaName
	fmt.Printf("Zeta '%v' created sucessfully !\n\n", zetaName)
	fmt.Printf("To run your function, use this url :\n> %v\n", zetaUrl)
}

var CreateCmd = &cobra.Command{
	Use:   "create [zeta_name] [filepath]",
	Short: "Create the zeta function",
	Long: `create the zeta function with the given 'zeta_name',
	using 'filepath' as the handler for the zeta`,
	Args: cobra.ExactArgs(2),
	Run:  createHandler,
}
