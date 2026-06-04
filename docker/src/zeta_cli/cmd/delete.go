package cmd

import (
	"fmt"
	"io"
	"strings"

	"net/http"

	"github.com/spf13/cobra"
	"github.com/zeta/constants"
)

func deleteHandler(cmd *cobra.Command, args []string) {
	zetaName := args[0]
	url := constants.Url
	request, err := http.NewRequest(
		http.MethodDelete,
		url+"/zeta/"+zetaName,
		nil,
	)
	if err != nil {
		fmt.Printf("Unable to create a new delete request\n")
		fmt.Println(err)
	}

	client := &http.Client{}
	resp, err := client.Do(request)
	if err != nil {
		fmt.Printf("Unable to delete the zeta '%v'\n", zetaName)
		fmt.Println(err)
	}
	statusCode := strings.Split(resp.Status, " ")[0]
	if statusCode != "204" {
		fmt.Printf("Error creating the zeta function\n")
		fmt.Printf("> status code: %v\n", resp.Status)
		body, err := io.ReadAll(resp.Body)
		if err == nil {
			fmt.Printf("> body: %v\n", string(body))
		}
		defer resp.Body.Close()
		return
	}

	fmt.Printf("Deleted '%v' sucessfully\n", zetaName)
}

var DeleteCmd = &cobra.Command{
	Use:   "delete [zeta_name]",
	Short: "Delete the zeta function",
	Long:  "delete the zeta function with the given 'zeta_name'",
	Args:  cobra.ExactArgs(1),
	Run:   deleteHandler,
}
