package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var VersionCmd = &cobra.Command{
	Use:   "version",
	Short: "Get the zeta version",
	Run: func(cmd *cobra.Command, args []string) {
		const ZETA_VERSION string = "v1.0.0"
		fmt.Printf("zeta functions version %v\n", ZETA_VERSION)
	},
}
