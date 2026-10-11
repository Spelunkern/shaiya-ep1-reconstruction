// Produce review evidence for one function from an existing baseline project.
// @category Shaiya
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
import java.io.*;
import java.security.MessageDigest;
public class ExportBlock extends GhidraScript {
    public void run() throws Exception {
        String[] args = getScriptArgs();
        long rva = Long.decode(args[0]);
        Path out = Paths.get(args[1]); Files.createDirectories(out);
        Function f = getFunctionAt(currentProgram.getImageBase().add(rva));
        if (f == null) throw new IOException("No function at RVA " + args[0]);
        if (!currentProgram.getExecutableSHA256().equalsIgnoreCase(args[2]))
            throw new IOException("Local project belongs to another original binary");
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        AddressRangeIterator ranges = f.getBody().getAddressRanges();
        while (ranges.hasNext()) {
            AddressRange range = ranges.next();
            Address address = range.getMinAddress();
            long remaining = range.getLength();
            while (remaining > 0) {
                int n = (int)Math.min(remaining, 65536);
                byte[] bytes = new byte[n];
                if (currentProgram.getMemory().getBytes(address, bytes) != n)
                    throw new IOException("Incomplete function body bytes");
                digest.update(bytes); remaining -= n;
                if (remaining > 0) address = address.add(n);
            }
        }
        StringBuilder bodyHash = new StringBuilder();
        for (byte b : digest.digest()) bodyHash.append(String.format("%02x", b & 255));
        if (!bodyHash.toString().equalsIgnoreCase(args[3]))
            throw new IOException("Function body differs from frozen baseline");
        try (BufferedWriter w = Files.newBufferedWriter(out.resolve("listing.txt"))) {
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction i = it.next();
                StringBuilder bytes = new StringBuilder();
                for (byte b : i.getBytes()) bytes.append(String.format("%02x", b & 255));
                w.write(i.getAddress() + "  " + bytes + "  " + i.toString() + "\n");
            }
        }
        DecompInterface decompiler = new DecompInterface();
        try {
            if (!decompiler.openProgram(currentProgram)) throw new IOException("Decompiler open failed");
            DecompileResults result = decompiler.decompileFunction(f, 120, monitor);
            if (!result.decompileCompleted() || result.getDecompiledFunction() == null)
                throw new IOException("Decompiler failed: " + result.getErrorMessage());
            Files.writeString(out.resolve("decompiled.c"), result.getDecompiledFunction().getC());
        } finally { decompiler.dispose(); }
        println("SHAIYA_BLOCK_EXPORTED " + args[0]);
    }
}
