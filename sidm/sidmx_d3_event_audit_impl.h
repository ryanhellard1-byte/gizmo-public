#ifndef SIDMX_D3_EVENT_AUDIT_IMPL_H
#define SIDMX_D3_EVENT_AUDIT_IMPL_H

/* Accepted-event identity audit for D3 commissioning.
 *
 * Each accepted collision contributes a deterministic 64-bit key derived from
 * the unordered pair IDs, synchronized integer time, D3 mode, and channel.
 * Per-rank XOR and modulo-2^64 sum digests are both recorded. Together with
 * the event count this catches changed, duplicated, or missing accepted pairs
 * while remaining independent of MPI rank ownership and event ordering.
 */
static volatile unsigned long long sidmx_d3_event_count[3] = {0,0,0};
static volatile unsigned long long sidmx_d3_event_xor[3] = {0,0,0};
static volatile unsigned long long sidmx_d3_event_sum[3] = {0,0,0};
static int sidmx_d3_event_audit_registered = 0;
static int sidmx_d3_event_audit_mode = 0;

static unsigned long long sidmx_d3_event_key(unsigned long long id_i,
                                              unsigned long long id_j,
                                              unsigned long long ti,
                                              int mode, int ch)
{
    const unsigned long long lo = id_i < id_j ? id_i : id_j;
    const unsigned long long hi = id_i < id_j ? id_j : id_i;
    unsigned long long x = 0x3f84d5b5b5470917ULL;
    x ^= sidmx_d3_mix64(lo + 0x9e3779b97f4a7c15ULL);
    x ^= sidmx_d3_mix64(hi + 0xbf58476d1ce4e5b9ULL);
    x ^= sidmx_d3_mix64(ti + 0x94d049bb133111ebULL);
    x ^= sidmx_d3_mix64(((unsigned long long)(unsigned int)mode << 32) ^
                        (unsigned long long)(unsigned int)ch ^ 0x6a09e667f3bcc909ULL);
    return sidmx_d3_mix64(x);
}

void sidmx_d3_note_collision_event(int ch,
                                   unsigned long long id_i,
                                   unsigned long long id_j,
                                   unsigned long long ti,
                                   int mode)
{
    unsigned long long key;
    if(ch < 0 || ch > 2) return;
    key = sidmx_d3_event_key(id_i,id_j,ti,mode,ch);
    sidmx_d3_note_collision(ch);
    __sync_fetch_and_add(&sidmx_d3_event_count[ch],1ULL);
    __sync_fetch_and_xor(&sidmx_d3_event_xor[ch],key);
    __sync_fetch_and_add(&sidmx_d3_event_sum[ch],key);
}

static void sidmx_d3_event_audit_dump(void)
{
    static const char *names[3] = {"HH","LL","HL"};
    char path[2048];
    const char *od = All.OutputDir;
    size_t n = strlen(od);
    FILE *fd;
    int ch;

    if(sidmx_d3_event_audit_mode <= 0) return;
    if(n > 0 && od[n-1] == '/')
        snprintf(path,sizeof(path),"%ssidmx_d3_event_digest.rank%05d.tsv",od,ThisTask);
    else
        snprintf(path,sizeof(path),"%s/sidmx_d3_event_digest.rank%05d.tsv",od,ThisTask);

    fd = fopen(path,"w");
    if(!fd)
    {
        fprintf(stderr,"SIDMx-D3: warning could not write event digest %s\n",path);
        return;
    }
    fprintf(fd,"mode\trank\tchannel\taccepted_events\tevent_xor_hex\tevent_sum_hex\n");
    for(ch=0;ch<3;ch++)
    {
        const unsigned long long nc = __sync_fetch_and_add(&sidmx_d3_event_count[ch],0ULL);
        const unsigned long long xx = __sync_fetch_and_add(&sidmx_d3_event_xor[ch],0ULL);
        const unsigned long long ss = __sync_fetch_and_add(&sidmx_d3_event_sum[ch],0ULL);
        fprintf(fd,"%d\t%d\t%s\t%llu\t%016llx\t%016llx\n",
                sidmx_d3_event_audit_mode,ThisTask,names[ch],nc,xx,ss);
    }
    fclose(fd);
}

void sidmx_d3_event_audit_init(void)
{
    int ch;
    sidmx_d3_event_audit_mode = sidmx_d3_runtime_mode();
    if(sidmx_d3_event_audit_mode <= 0) return;
    for(ch=0;ch<3;ch++)
    {
        sidmx_d3_event_count[ch]=0;
        sidmx_d3_event_xor[ch]=0;
        sidmx_d3_event_sum[ch]=0;
    }
    if(!sidmx_d3_event_audit_registered)
    {
        if(atexit(sidmx_d3_event_audit_dump) != 0)
        {
            if(ThisTask == 0) fprintf(stderr,"SIDMx-D3: failed to register event digest dump\n");
            endrun(171206);
        }
        sidmx_d3_event_audit_registered=1;
    }
}

#endif /* SIDMX_D3_EVENT_AUDIT_IMPL_H */
