package cmd

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/spf13/cobra"
	"github.com/zeta/constants"
)

func ListHandler(cmd *cobra.Command, args []string) {
	url := constants.Url
	path := "/zeta/meta"
	resp, err := http.Get(url + path)
	if err != nil {
		fmt.Printf("Unable to retrieve zeta information\n")
		return
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Unable to read response body\n")
	}

	var myBody []map[string]interface{}
	errjson := json.Unmarshal(body, &myBody)
	if errjson != nil {
		fmt.Printf("Unable to parse json\n")
		fmt.Println(errjson)
		return
	}

	fmt.Println("List of the created zetas")
	fmt.Println("=========================")
	for _, zeta := range myBody {
		name := zeta["name"]
		fmt.Printf("- %v\n", name)
	}
}

var ListCmd = &cobra.Command{
	Use:     "list",
	Aliases: []string{"ls"},
	Short:   "List the created zeta function names",
	Long:    "List the created zeta function names",
	Run:     ListHandler,
}
