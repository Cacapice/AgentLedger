package agentledger

import (
	"errors"
	"sync"
	"time"
)

type RunStatus string

const (
	Pending   RunStatus = "PENDING"
	Running   RunStatus = "RUNNING"
	Waiting   RunStatus = "WAITING"
	Succeeded RunStatus = "SUCCEEDED"
	Failed    RunStatus = "FAILED"
	Cancelled RunStatus = "CANCELLED"
)

type RunState struct {
	RunID      string
	Status     RunStatus
	Step       string
	Checkpoint any
	LeaseToken string
	LeaseOwner string
	Revision   int
	UpdatedAt  time.Time
}
type Store struct {
	mu   sync.Mutex
	runs map[string]RunState
}

func NewStore() *Store { return &Store{runs: map[string]RunState{}} }
func (s *Store) Create(id string) (RunState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.runs[id]; ok {
		return RunState{}, errors.New("run exists")
	}
	r := RunState{RunID: id, Status: Pending, UpdatedAt: time.Now().UTC()}
	s.runs[id] = r
	return r, nil
}
func (s *Store) Acquire(id, owner, token string) (RunState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	r, ok := s.runs[id]
	if !ok {
		return r, errors.New("unknown run")
	}
	r.Status = Running
	r.LeaseOwner = owner
	r.LeaseToken = token
	r.Revision++
	r.UpdatedAt = time.Now().UTC()
	s.runs[id] = r
	return r, nil
}
func (s *Store) Checkpoint(id, token, step string, checkpoint any) (RunState, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	r, ok := s.runs[id]
	if !ok {
		return r, errors.New("unknown run")
	}
	if r.LeaseToken == "" || r.LeaseToken != token {
		return r, errors.New("stale fencing token")
	}
	r.Step = step
	r.Checkpoint = checkpoint
	r.Revision++
	r.UpdatedAt = time.Now().UTC()
	s.runs[id] = r
	return r, nil
}

var transitions = map[string]map[string]bool{"PROPOSED": {"AUTHORIZED": true, "CANCELLED": true}, "AUTHORIZED": {"ATTEMPTED": true, "CANCELLED": true}, "ATTEMPTED": {"COMMITTED": true, "FAILED": true, "UNKNOWN": true}, "UNKNOWN": {"COMMITTED": true, "FAILED": true}}

func ValidTransition(from, to string) bool { return transitions[from][to] }
