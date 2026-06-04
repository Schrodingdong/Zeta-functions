package cmd

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/spf13/cobra"
	"github.com/zeta/constants"
)

func PsHandler(cmd *cobra.Command, args []string) {
	var specifiedZeta string
	if len(args) >= 1 {
		specifiedZeta = args[0]
	}
	url := constants.Url
	path := "/zeta/meta/" + specifiedZeta
	resp, err := http.Get(url + path)
	if err != nil {
		fmt.Printf("Unable to retrieve zeta information\n")
		return
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Unable to read response body\n")
	}

	// Pretty print json body
	var indentedJsonBody bytes.Buffer
	err = json.Indent(&indentedJsonBody, body, "", "  ")
	if err != nil {
		fmt.Printf("Unable to format json\n")
		fmt.Println(err)
		return
	}
	fmt.Println(indentedJsonBody.String())
}

var PsCmd = &cobra.Command{
	Use:   "ps [zeta_name]",
	Short: "List zeta metadata",
	Long:  "List zeta metadata. if zeta_name is specified, list its own metadata.",
	Run:   PsHandler,
}
