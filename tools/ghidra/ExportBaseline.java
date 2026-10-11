// Export immutable function boundaries and call references; no decompiler guesses.
// @category Shaiya
import ghidra.app.script.GhidraScript;
import ghidra.app.util.headless.HeadlessScript;
import ghidra.framework.Application;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import com.google.gson.*;
import java.nio.file.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.*;

public class ExportBaseline extends HeadlessScript {
    private long base;
    private long rva(Address a) { return a.getOffset() - base; }
    private String hex(byte[] bytes) {
        StringBuilder s = new StringBuilder();
        for (byte b : bytes) s.append(String.format("%02x", b & 255));
        return s.toString();
    }
    public void run() throws Exception {
        Path out = Paths.get(getScriptArgs()[0]);
        Files.createDirectories(out);
        base = currentProgram.getImageBase().getOffset();
        Gson gson = new GsonBuilder().disableHtmlEscaping().create();
        int count = 0;
        try (BufferedWriter writer = Files.newBufferedWriter(out.resolve("functions.jsonl"))) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext()) {
                monitor.checkCancelled();
                Function f = it.next();
                if (f.isExternal()) continue;
                JsonObject obj = new JsonObject();
                obj.addProperty("entry_rva", rva(f.getEntryPoint()));
                obj.addProperty("name", f.getName());
                obj.addProperty("signature", f.getSignature().toString());
                obj.addProperty("calling_convention", f.getCallingConventionName());
                obj.addProperty("thunk", f.isThunk());
                JsonArray ranges = new JsonArray();
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                AddressRangeIterator rit = f.getBody().getAddressRanges();
                while (rit.hasNext()) {
                    AddressRange range = rit.next();
                    JsonArray pair = new JsonArray();
                    pair.add(rva(range.getMinAddress()));
                    pair.add(rva(range.getMaxAddress()) + 1);
                    ranges.add(pair);
                    Address a = range.getMinAddress();
                    long remaining = range.getLength();
                    while (remaining > 0) {
                        int n = (int)Math.min(remaining, 65536);
                        byte[] bytes = new byte[n];
                        if (currentProgram.getMemory().getBytes(a, bytes) != n)
                            throw new IOException("Incomplete function bytes: " + f.getEntryPoint());
                        digest.update(bytes);
                        remaining -= n;
                        if (remaining > 0) a = a.add(n);
                    }
                }
                obj.add("ranges", ranges);
                obj.addProperty("body_sha256", hex(digest.digest()));
                TreeSet<Long> calls = new TreeSet<>();
                TreeSet<String> external = new TreeSet<>();
                TreeSet<Long> dataRefs = new TreeSet<>();
                int instructions = 0, indirect = 0;
                InstructionIterator ins = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (ins.hasNext()) {
                    Instruction i = ins.next(); instructions++;
                    if (i.getFlowType().isCall() && i.getFlowType().isComputed()) indirect++;
                    for (Reference ref : i.getReferencesFrom()) {
                        if (ref.getReferenceType().isData() && ref.getToAddress().isMemoryAddress())
                            dataRefs.add(rva(ref.getToAddress()));
                        if (!ref.getReferenceType().isCall() && !ref.getReferenceType().isJump()) continue;
                        if (f.getBody().contains(ref.getToAddress())) continue;
                        Function callee = getFunctionAt(ref.getToAddress());
                        if (callee != null && callee.isExternal()) external.add(callee.getName(true));
                        else if (ref.getToAddress().isMemoryAddress()) calls.add(rva(ref.getToAddress()));
                    }
                }
                JsonArray callArray = new JsonArray(); for (long c : calls) callArray.add(c);
                JsonArray extArray = new JsonArray(); for (String c : external) extArray.add(c);
                JsonArray dataArray = new JsonArray(); for (long d : dataRefs) dataArray.add(d);
                obj.add("data_refs_rva", dataArray);
                obj.add("calls_rva", callArray); obj.add("external_calls", extArray);
                obj.addProperty("instruction_count", instructions);
                obj.addProperty("indirect_call_count", indirect);
                writer.write(gson.toJson(obj)); writer.newLine(); count++;
            }
        }
        JsonObject summary = new JsonObject();
        summary.addProperty("ghidra_version", Application.getApplicationVersion());
        summary.addProperty("program_sha256", currentProgram.getExecutableSHA256());
        summary.addProperty("language", currentProgram.getLanguageID().toString());
        summary.addProperty("compiler_spec", currentProgram.getCompilerSpec().getCompilerSpecID().toString());
        summary.addProperty("image_base", base);
        summary.addProperty("function_count", count);
        summary.addProperty("analysis_timed_out", analysisTimeoutOccurred());
        Files.writeString(out.resolve("summary.json"), gson.toJson(summary) + "\n");
        println("SHAIYA_BASELINE_EXPORTED " + count);
    }
}
