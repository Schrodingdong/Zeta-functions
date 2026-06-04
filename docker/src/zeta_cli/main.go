package main

import (
	"github.com/spf13/cobra"
	"github.com/zeta/cmd"
)

func main() {
	VersionCmd := cmd.VersionCmd
	CreateCmd := cmd.CreateCmd
	DeleteCmd := cmd.DeleteCmd
	ListCmd := cmd.ListCmd
	PsCmd := cmd.PsCmd

	// Collect the cmds
	var rootCmd = &cobra.Command{Use: "zeta [CMD]"}
	rootCmd.AddCommand(VersionCmd)
	rootCmd.AddCommand(CreateCmd)
	rootCmd.AddCommand(DeleteCmd)
	rootCmd.AddCommand(ListCmd)
	rootCmd.AddCommand(PsCmd)

	// Execute
	rootCmd.Execute()
}
