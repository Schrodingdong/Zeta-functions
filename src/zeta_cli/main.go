package main

import (
	"github.com/spf13/cobra"
	"github.com/zeta/cmd"
)

func main() {
	VersionCmd := cmd.VersionCmd
	CreateCmd := cmd.CreateCmd

	// Collect the cmds
	var rootCmd = &cobra.Command{Use: "zeta"}
	rootCmd.AddCommand(VersionCmd)
	rootCmd.AddCommand(CreateCmd)

	// Execute
	rootCmd.Execute()
}
