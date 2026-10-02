package main

import (
	"encoding/json"
	"fmt"
	al "github.com/Cacapice/AgentLedger/go/agentledger"
	"os"
)

type Fixture struct {
	Cases []struct {
		Name        string   `json:"name"`
		Transitions []string `json:"transitions"`
		Valid       bool     `json:"valid"`
	} `json:"cases"`
}

func main() {
	if len(os.Args) < 3 || os.Args[1] != "conformance" {
		fmt.Println("usage: agentledger-go conformance <fixture>")
		return
	}
	b, e := os.ReadFile(os.Args[2])
	if e != nil {
		panic(e)
	}
	var f Fixture
	if e = json.Unmarshal(b, &f); e != nil {
		panic(e)
	}
	for _, c := range f.Cases {
		ok := true
		for i := 1; i < len(c.Transitions); i++ {
			if !al.ValidTransition(c.Transitions[i-1], c.Transitions[i]) {
				ok = false
			}
		}
		if ok != c.Valid {
			panic("conformance failed: " + c.Name)
		}
	}
	fmt.Println("Go conformance: OK")
}
