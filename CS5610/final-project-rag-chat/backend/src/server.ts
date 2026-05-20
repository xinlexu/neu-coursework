// ============================================================================================================
// RAG Chat Server (Dual Mode: Gemini & OpenAI)
// ============================================================================================================

import express, { Request, Response, NextFunction } from 'express';
import session from 'express-session';
import bcrypt from 'bcrypt';
import cors from 'cors';
import crypto from 'crypto';
import https from 'https';
import http from 'http';
import { IncomingMessage } from 'http';
import { QdrantClient } from '@qdrant/js-client-rest';
import { EmbeddingModel, FlagEmbedding } from 'fastembed';
import multer from 'multer';
import fs from 'fs';
import path from 'path';
import 'dotenv/config';
import OpenAI from 'openai';

// ============================================================================================================
// 1. Global configuration
// ============================================================================================================

const DEFAULT_THRESHOLD = 0.6;

const CONFIG = {
	host: process.env.HOST || '0.0.0.0',
	port: parseInt(process.env.PORT || '5500', 10),
	staticDir: process.env.STATIC_DIR || './dist',
	sessionSecret: process.env.SESSION_SECRET || 'change-this-in-production',
	sessionMaxAge: 7 * 24 * 60 * 60 * 1000,
	llm: {
		gemini: {
			apiKey: process.env.GEMINI_API_KEY || '',
			model: process.env.GEMINI_MODEL || 'gemini-2.0-flash-exp',
			host: 'generativelanguage.googleapis.com',
			pathBase: '/v1beta/models',
		},
		openai: {
			apiKey: process.env.OPENAI_API_KEY || '',
			model: process.env.OPENAI_MODEL || 'gpt-4o-mini'
		}
	},
	qdrant: {
		host: process.env.QDRANT_HOST || 'localhost',
		port: parseInt(process.env.QDRANT_PORT || '6333', 10),
		collections: { users: 'users', chats: 'chats', documents: 'documents' },
		vectorSize: 384,
	},
	embedding: {
		model: EmbeddingModel.BGESmallENV15,
		cacheDir: process.env.EMBEDDING_CACHE_DIR || './.cache/embeddings'
	},
	upload: {
		dir: './uploads',
		chunkSize: 500,
		chunkOverlap: 100
	}
} as const;

// ============================================================================================================
// 2. Data models 
// ============================================================================================================

declare module 'express-session' {
	interface SessionData {
		userId: string;
		username: string;
	}
}

interface User {
	userId: string;
	username: string;
	passwordHash: string;
	createdAt: string;
}

interface Message {
	role: 'user' | 'assistant';
	content: string;
	timestamp: string;
	references?: Reference[];
}

interface ChatSettings {
	professionalMode: boolean;
	topK: number;
	similarityThreshold: number;
}

interface Chat {
	chatId: string;
	userId: string;
	messages: Message[];
	preview: string;
	settings: ChatSettings;
	createdAt: string;
	updatedAt: string;
}

interface Document {
	srcId: string;
	docId: string;
	userId: string;
	title: string;
	author?: string;
	page?: number;
	content: string;
	createdAt: string;
}

interface Reference {
	refId: string;
	title: string;
	author?: string;
	page?: number;
	content: string;
	score: number;
}

// ============================================================================================================
// 3. Client Setup
// ============================================================================================================

const qdrant = new QdrantClient({ host: CONFIG.qdrant.host, port: CONFIG.qdrant.port });

let openai: OpenAI | null = null;
if (CONFIG.llm.openai.apiKey) {
	openai = new OpenAI({ apiKey: CONFIG.llm.openai.apiKey });
	console.log('[Server] OpenAI client initialized (Fallback)');
}

const hasGemini = !!CONFIG.llm.gemini.apiKey;
const hasOpenAI = !!CONFIG.llm.openai.apiKey;

// ============================================================================================================
// 4. Collection Setup (Database)
// ============================================================================================================

async function resetAllCollections(): Promise<void> {
	const { collections } = await qdrant.getCollections();
	for (const col of collections) {
		if (col.name == "users" || col.name == "chats" || col.name == "documents") {
			await qdrant.deleteCollection(col.name);
			console.log(`[Qdrant] Collection '${col.name}' deleted.`);
		}
	}
	const { vectorSize, collections: cols } = CONFIG.qdrant;
	await qdrant.createCollection(cols.users, { 
		vectors: { size: vectorSize, distance: 'Cosine', on_disk: true }
	});
	console.log(`[Qdrant] Collection '${cols.users}' created.`);
	await qdrant.createCollection(cols.chats, { 
		vectors: { size: vectorSize, distance: 'Cosine', on_disk: true }
	});
	console.log(`[Qdrant] Collection '${cols.chats}' created.`);
	await qdrant.createCollection(cols.documents, { 
		vectors: { size: vectorSize, distance: 'Cosine', on_disk: true } 
	});
	console.log(`[Qdrant] Collection '${cols.documents}' created.`);
}

async function ensureCollection(name: string, vectorSize: number, onDisk = false): Promise<void> {
	const { collections } = await qdrant.getCollections();
	if (collections.some(c => c.name === name)) {
		console.log(`[Qdrant] Collection '${name}' exists.`);
		return;
	}
	console.log(`[Qdrant] Collection '${name}' does not exist, creating '${name}' ...`);
	await qdrant.createCollection(name, { vectors: { size: vectorSize, distance: 'Cosine', on_disk: onDisk } });
	console.log(`[Qdrant] Collection ${name} created.`);
}

// ============================================================================================================
// 5. Embedder Setup
// ============================================================================================================

let embedder: FlagEmbedding;

async function initEmbedder(): Promise<void> {
	console.log(`[FastEmbed] Loading model '${CONFIG.embedding.model}'...`);
	embedder = await FlagEmbedding.init({
		model: CONFIG.embedding.model,
		cacheDir: CONFIG.embedding.cacheDir
	});
	console.log(`[FastEmbed] Model '${CONFIG.embedding.model}' ready.`);
}

async function collectGenerator<T>(gen: AsyncGenerator<T[], void, unknown>): Promise<T[]> {
	const results: T[] = [];
	for await (const batch of gen) {
		results.push(...batch);
	}
	return results;
}

async function getEmbedding(text: string): Promise<number[]> {
	if (!embedder) { throw new Error('Embedder is not initialized'); }
	const embeddings = await collectGenerator(embedder.embed([text]));
	return Array.from(embeddings[0]);
}

async function getEmbeddingBatch(texts: string[]): Promise<number[][]> {
	if (!embedder) { throw new Error('Embedder is not initialized'); }
	const embeddings = await collectGenerator(embedder.embed(texts));
	return embeddings.map(emb => Array.from(emb));
}

function isEmbedderReady(): boolean {
	return embedder !== undefined && embedder !== null;
}

// ============================================================================================================
// 6. User Store
// ============================================================================================================

const UserStore = {
	collection: CONFIG.qdrant.collections.users,
	embeddingDim: CONFIG.qdrant.vectorSize,

	async init() {
		await ensureCollection(this.collection, this.embeddingDim, true);
		await qdrant.createPayloadIndex(this.collection, { field_name: 'username', field_schema: 'keyword' }).catch(() => {});
		console.log(`[Qdrant][${this.collection}] Initialized.`);
	},

	async getByUsername(username: string): Promise<User | null> {
		try {
			const { points } = await qdrant.scroll(this.collection, {
				filter: { must: [{ key: 'username', match: { value: username.toLowerCase() } }] },
				limit: 1,
				with_payload: true
			});
			if (points[0]?.payload) {
				return points[0].payload as unknown as User;
			}
			return null;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error getting user by username:`, err);
			return null;
		}
	},

	async getByUserId(userId: string): Promise<User | null> {
		try {
			const points = await qdrant.retrieve(this.collection, { ids: [userId], with_payload: true });
			if (points[0]?.payload) {
				return points[0].payload as unknown as User;
			}
			return null;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error getting user by id:`, err);
			return null;
		}
	},

	async create(data: { userId: string; username: string; passwordHash: string }): Promise<User | null> {
		try {
			const user: User = { ...data, username: data.username.toLowerCase(), createdAt: new Date().toISOString() };
			const vector = Array(this.embeddingDim).fill(0);
			await qdrant.upsert(this.collection, { points: [{ id: data.userId, vector, payload: user as unknown as Record<string, unknown> }] });
			console.log(`[Qdrant][${this.collection}] Created user: ${data.username}`);
			return user;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error creating user:`, err);
			return null;
		}
	},

	async exists(username: string): Promise<boolean> {
		const user = await this.getByUsername(username.toLowerCase());
		return !!user;
	}
};

// ============================================================================================================
// 7. Chat Store
// ============================================================================================================

const ChatStore = {
	collection: CONFIG.qdrant.collections.chats,
	embeddingDim: CONFIG.qdrant.vectorSize,

	async init() {
		await ensureCollection(this.collection, this.embeddingDim, true);
		await qdrant.createPayloadIndex(this.collection, { field_name: 'userId', field_schema: 'keyword' }).catch(() => {});
		console.log(`[Qdrant][${this.collection}] Initialized.`);
	},

	async getByChatId(chatId: string): Promise<Chat | null> {
		try {
			const points = await qdrant.retrieve(this.collection, { ids: [chatId], with_payload: true });
			if (points[0]?.payload) {
				return points[0].payload as unknown as Chat;
			}
			return null;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error getting chat by id:`, err);
			return null;
		}
	},

	async listByUserId(userId: string, limit: number = 100): Promise<Chat[]> {
		try {
			let offset: string | number | Record<string, unknown> | null | undefined;
			let allChats: Chat[] = [];
			do {
				const response = await qdrant.scroll(this.collection, {
					filter: { must: [{ key: 'userId', match: { value: userId } }] },
					limit: limit,
					with_payload: true,
					offset,
				});
				const chats = response.points.map(p => p.payload as unknown as Chat);
				allChats.push(...chats);
				offset = response.next_page_offset;
			} while (offset);
			allChats.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
			return allChats;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error listing chats:`, err);
			return [];
		}
	},

	async create(data: { chatId: string; userId: string; settings: ChatSettings }): Promise<Chat | null> {
		try {
			const now = new Date().toISOString();
			const chat: Chat = {
				chatId: data.chatId,
				userId: data.userId,
				messages: [],
				preview: 'New chat',
				settings: data.settings,
				createdAt: now,
				updatedAt: now
			};
			const vector = Array(this.embeddingDim).fill(0);
			await qdrant.upsert(this.collection, {
				points: [{ id: data.chatId, vector, payload: chat as unknown as Record<string, unknown> }]
			});
			console.log(`[Qdrant][${this.collection}] Created chat: ${data.chatId}`);
			return chat;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error creating chat:`, err);
			return null;
		}
	},

	async update(chatId: string, updates: Partial<Chat>): Promise<Chat | null> {
		try {
			const existing = await this.getByChatId(chatId);
			if (!existing) return null;
			const updated: Chat = { ...existing, ...updates, updatedAt: new Date().toISOString() };
			const vector = Array(this.embeddingDim).fill(0);
			await qdrant.upsert(this.collection, {
				points: [{ id: chatId, vector, payload: updated as unknown as Record<string, unknown> }]
			});
			return updated;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error updating chat:`, err);
			return null;
		}
	},

	async delete(chatId: string, userId: string): Promise<boolean> {
		try {
			const chat = await this.getByChatId(chatId);
			if (!chat || chat.userId !== userId) return false;
			await qdrant.delete(this.collection, { points: [chatId] });
			console.log(`[Qdrant][${this.collection}] Deleted chat: ${chatId}`);
			return true;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error deleting chat:`, err);
			return false;
		}
	}
};

// ============================================================================================================
// 8. Document Store
// ============================================================================================================

const DocumentStore = {
	collection: CONFIG.qdrant.collections.documents,
	embeddingDim: CONFIG.qdrant.vectorSize,

	async init() {
		await ensureCollection(this.collection, this.embeddingDim, true);
		await qdrant.createPayloadIndex(this.collection, { field_name: 'title', field_schema: 'text' }).catch(() => {});
		await qdrant.createPayloadIndex(this.collection, { field_name: 'author', field_schema: 'keyword' }).catch(() => {});
		await qdrant.createPayloadIndex(this.collection, { field_name: 'userId', field_schema: 'keyword' }).catch(() => {});
		console.log(`[Qdrant][${this.collection}] Initialized.`);
	},

	async search(query: string, userId: string, topK = 5, minScore = 0): Promise<Reference[]> {
		try {
			const vector = await getEmbedding(query);
			const results = await qdrant.search(this.collection, {
				vector,
				filter: { must: [{ key: 'userId', match: { value: userId } }] },
				limit: topK,
				score_threshold: minScore,
				with_payload: true
			});
			const sorted = results.sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
			const references: Reference[] = sorted.map((hit, index) => {
				const p = hit.payload as unknown as Document;
				return {
					refId: (index + 1).toString(),
					title: p.title,
					author: p.author,
					page: p.page,
					content: p.content,
					score: hit.score ?? 0
				} as Reference;
			});
			console.log(`[Qdrant][${this.collection}] Retrieved ${references.length} references (topK=${topK}, minScore=${minScore})`);
			return references;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error searching:`, err);
			return [];
		}
	},

	async createBatch(docs: Document[]): Promise<boolean> {
		try {
			if (!isEmbedderReady()) {
				console.error(`[FastEmbed] Embedder not ready`);
				return false;
			}
			const vectors = await getEmbeddingBatch(docs.map(d => d.content));
			const points = docs.map((doc, i) => ({
				id: doc.docId,
				vector: vectors[i],
				payload: { ...doc, createdAt: new Date().toISOString() } as Record<string, unknown>
			}));
			await qdrant.upsert(this.collection, { points });
			console.log(`[Qdrant][${this.collection}] Created ${docs.length} documents.`);
			return true;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error creating batch:`, err);
			return false;
		}
	},

	async deleteByUserId(userId: string): Promise<boolean> {
		try {
			await qdrant.delete(this.collection, {
				filter: {
					must: [{ key: 'userId', match: { value: userId } }]
				}
			});
			console.log(`[Qdrant][${this.collection}] Deleted all documents for user ${userId}.`);
			return true;
		} catch (err) {
			console.error(`[Qdrant][${this.collection}] Error deleting documents for user ${userId}:`, err);
			return false;
		}
	}
};

// ============================================================================================================
// 9. RAG Helpers
// ============================================================================================================

function buildRAGContext(refs: Reference[]): string {
	if (!refs?.length) return '';
	return '\n\nReferences:\n' + refs.map((ref) =>
		`[${ref.refId}] ${ref.title} by ${ref.author}, p.${ref.page} (${(ref.score * 100).toFixed(1)}%):\n${ref.content}`
	).join('\n\n') + '\n\nUse these references to answer. Cite with [1], [2], etc.';
}

function createSystemPrompt(professionalMode: boolean, hasReferences: boolean): string {
	if (!professionalMode) {
		return `You are a helpful AI assistant. Provide clear, accurate, and helpful responses.`;
	}
	if (hasReferences) {
		return `You are a RAG (Retrieval-Augmented Generation) assistant.
IMPORTANT INSTRUCTIONS:
1. Never make up information - ONLY use what's in the references.
2. If the references are not relevant to the user's question, respond with: "I don't have enough relevant information in my knowledge base to answer this question."
3. When you use information from a reference, cite it using [1], [2], etc. If you use multiple references for a single sentence, list them in order using [1][2][3], etc.
4. If you can partially answer the user's question, do so and acknowledge the limitations.
Be helpful and professional in your responses.`;
	} else {
		return `You are a RAG (Retrieval-Augmented Generation) assistant. No relevant documents were found in the knowledge base for user's question.
IMPORTANT INSTRUCTIONS:
1. ALWAYS respond with the DEFAULT message: "I don't have any relevant documents in my knowledge base to answer this question. Please try:
1. Uploading relevant documents
2. Adjusting the similarity threshold in settings
3. Rephrasing your question"
2. Regardless of the user's question, DO NOT attempt to provide any other information.`;
	}
}

// ============================================================================================================
// 10. LLM API (Dual Support: Gemini & OpenAI)
// ============================================================================================================

async function* streamGemini(
	messages: Message[],
	systemPrompt: string,
	ragContext?: string,
	signal?: AbortSignal
): AsyncGenerator<string> {
	const contents = messages.map((msg, index) => {
		const isLastMessage = index === messages.length - 1;
		const isUser = msg.role === 'user';
		let text = msg.content;
		if (isLastMessage && isUser && ragContext) {
			text += ragContext;
		}
		return {
			role: isUser ? 'user' : 'model',
			parts: [{ text }]
		};
	});

	const payload: any = { contents };
	if (systemPrompt) {
		payload.systemInstruction = { parts: [{ text: systemPrompt }] };
	}

	const streamPromise = new Promise<IncomingMessage>((resolve, reject) => {
		const req = https.request({
			hostname: CONFIG.llm.gemini.host,
			port: 443,
			path: `${CONFIG.llm.gemini.pathBase}/${encodeURIComponent(CONFIG.llm.gemini.model)}:streamGenerateContent?alt=sse`,
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'x-goog-api-key': CONFIG.llm.gemini.apiKey
			}
		}, resolve);

		if (signal) {
			signal.addEventListener('abort', () => {
				req.destroy();
				reject(new Error('Aborted'));
			});
		}
		req.on('error', reject);
		req.write(JSON.stringify(payload));
		req.end();
	});

	const stream = await streamPromise;

	for await (const chunk of stream) {
		const text = chunk.toString();
		for (const line of text.split('\n')) {
			if (line.startsWith('data: ')) {
				const data = line.slice(6);
				if (data === '[DONE]') continue;
				try {
					const parsed = JSON.parse(data);
					const content = parsed.candidates?.[0]?.content?.parts?.[0]?.text;
					if (content) {
						yield content;
					}
				} catch {}
			}
		}
	}
}

async function* streamOpenAI(
	messages: Message[],
	systemPrompt: string,
	ragContext?: string,
	signal?: AbortSignal
): AsyncGenerator<string> {
	if (!openai) throw new Error("OpenAI not configured");

	const apiMessages: any[] = [
		{ role: 'system', content: systemPrompt }
	];

	messages.forEach((msg, index) => {
		const isLastMessage = index === messages.length - 1;
		let content = msg.content;
		if (isLastMessage && msg.role === 'user' && ragContext) {
			content += `\n\n${ragContext}`;
		}
		apiMessages.push({
			role: msg.role === 'assistant' ? 'assistant' : 'user',
			content: content
		});
	});

	try {
		const stream = await openai.chat.completions.create({
			model: CONFIG.llm.openai.model,
			messages: apiMessages,
			stream: true,
		}, { signal });

		for await (const chunk of stream) {
			const content = chunk.choices[0]?.delta?.content || '';
			if (content) {
				yield content;
			}
		}
	} catch (error: any) {
		if (error.name === 'AbortError') {
			throw new Error('Aborted');
		}
		throw error;
	}
}

// ============================================================================================================
// 11. Express App Setup
// ============================================================================================================

function requireAuth(req: Request, res: Response, next: NextFunction): void {
	if (!req.session.userId) {
		res.status(401).json({ error: 'Unauthorized' });
		return;
	}
	next();
}

const app = express();

// CORS - allows any origin with credentials
app.use(cors({
	origin: true,
	credentials: true
}));

app.use(express.json());

app.use(session({
	secret: CONFIG.sessionSecret,
	resave: false,
	saveUninitialized: false,
	cookie: {
		secure: false,
		httpOnly: true,
		maxAge: CONFIG.sessionMaxAge,
		sameSite: 'lax'
	}
}));

const upload = multer({
	storage: multer.memoryStorage(),
	limits: { fileSize: 10 * 1024 * 1024 }
}).single('file');

// ============================================================================================================
// 12. Auth Routes
// ============================================================================================================

app.post('/api/auth/signup', async (req: Request, res: Response) => {
	try {
		const { username, password } = req.body;
		if (!username || !password) {
			res.status(400).json({ message: 'Username and password required' });
			return;
		}
		if (username.length < 3) {
			res.status(400).json({ message: 'Username must be at least 3 characters' });
			return;
		}
		if (password.length < 6) {
			res.status(400).json({ message: 'Password must be at least 6 characters' });
			return;
		}

		const exists = await UserStore.exists(username);
		if (exists) {
			res.status(400).json({ message: 'Username already taken' });
			return;
		}

		const userId = crypto.randomUUID();
		const passwordHash = await bcrypt.hash(password, 10);
		const user = await UserStore.create({ userId, username, passwordHash });
		if (!user) {
			res.status(500).json({ message: 'Internal server error' });
			return;
		}

		req.session.userId = userId;
		req.session.username = user.username;
		res.json({ message: 'Account created', user: { username: user.username } });
		console.log(`[Server] Signup success: ${user.userId}, ${user.username}`);
	} catch (error) {
		console.error('[Server] Signup error:', error);
		res.status(500).json({ message: 'Internal server error' });
	}
});

app.post('/api/auth/signin', async (req: Request, res: Response) => {
	try {
		const { username, password } = req.body;
		if (!username || !password) {
			res.status(400).json({ message: 'Username and password required' });
			return;
		}

		const user = await UserStore.getByUsername(username);
		if (!user) {
			res.status(401).json({ message: 'Invalid username or password' });
			return;
		}

		const valid = await bcrypt.compare(password, user.passwordHash);
		if (!valid) {
			res.status(401).json({ message: 'Invalid username or password' });
			return;
		}

		req.session.userId = user.userId;
		req.session.username = user.username;
		res.json({ message: 'Signed in', user: { username: user.username } });
		console.log(`[Server] Signin success: ${user.userId}, ${user.username}`);
	} catch (error) {
		console.error('[Server] Signin error:', error);
		res.status(500).json({ message: 'Internal server error' });
	}
});

app.post('/api/auth/signout', (req: Request, res: Response) => {
	const userId = req.session.userId;
	req.session.destroy((error) => {
		if (error) {
			console.error(`[Server] Signout error for user ${userId}:`, error);
			return res.status(500).json({ message: 'Failed to sign out' });
		}
		res.clearCookie('connect.sid');
		res.json({ message: 'Signed out' });
		console.log(`[Server] Signout success for user ${userId}`);
	});
});

app.get('/api/auth/me', (req: Request, res: Response) => {
	if (!req.session.userId) {
		res.status(401).json({ error: 'Authentication failed' });
		return;
	}
	res.json({ user: { username: req.session.username } });
});

// ============================================================================================================
// 13. Chat Routes
// ============================================================================================================

app.get('/api/chats', requireAuth, async (req: Request, res: Response) => {
	try {
		const chatList = await ChatStore.listByUserId(req.session.userId!);
		const chats: object[] = chatList.map(chat => ({
			id: chat.chatId,
			preview: chat.preview,
			updatedAt: chat.updatedAt
		}));
		res.json({ chats });
	} catch (error) {
		console.error(`[Server] Load chats error for user ${req.session.userId}:`, error);
		res.status(500).json({ message: 'Failed to load chats' });
	}
});

app.post('/api/chats', requireAuth, async (req: Request, res: Response) => {
	try {
		const { settings } = req.body;
		const chatId = crypto.randomUUID();
		const chat = await ChatStore.create({
			chatId,
			userId: req.session.userId!,
			settings: settings || { professionalMode: false, topK: 5, similarityThreshold: 0 }
		});
		if (!chat) {
			res.status(500).json({ message: 'Failed to create chat' });
			return;
		}
		res.json({ chat });
		console.log(`[Server] Created chat ${chatId} for user ${req.session.userId}`);
	} catch (error) {
		console.error(`[Server] Create chat error for user ${req.session.userId}:`, error);
		res.status(500).json({ message: 'Failed to create chat' });
	}
});

app.get('/api/chats/:chatId', requireAuth, async (req: Request, res: Response) => {
	try {
		const chat = await ChatStore.getByChatId(req.params.chatId);
		if (!chat || chat.userId !== req.session.userId) {
			res.status(404).json({ message: 'Chat not found' });
			return;
		}
		res.json({ chat });
	} catch (error) {
		console.error(`[Server] Get chat error for user ${req.session.userId}:`, error);
		res.status(500).json({ message: 'Failed to load chat' });
	}
});

app.patch('/api/chats/:chatId', requireAuth, async (req: Request, res: Response) => {
	try {
		const { chatId } = req.params;
		const { settings, messages } = req.body;
		const userId = req.session.userId!;

		const chat = await ChatStore.getByChatId(chatId);
		if (!chat || chat.userId !== userId) {
			res.status(404).json({ message: 'Chat not found' });
			return;
		}

		const updates: Partial<Chat> = {};
		if (settings !== undefined) {
			updates.settings = settings;
		}
		if (messages !== undefined) {
			updates.messages = messages;
			if (chat.preview === 'New chat' && messages.length > 0) {
				const firstUserMsg = messages.find((m: Message) => m.role === 'user');
				if (firstUserMsg) {
					updates.preview = firstUserMsg.content.slice(0, 50) +
						(firstUserMsg.content.length > 50 ? '...' : '');
				}
			}
		}

		if (Object.keys(updates).length === 0) {
			res.json({ success: true, message: 'No fields to update' });
			return;
		}

		const updated = await ChatStore.update(chatId, updates);
		if (!updated) {
			res.status(500).json({ success: false, message: 'Failed to update chat' });
			return;
		}
		res.json({ success: true, message: `Chat updated: ${Object.keys(updates).join(', ')}` });
	} catch (error) {
		console.error(`[Server] Update chat error for chat ${req.params.chatId}:`, error);
		res.status(500).json({ success: false, message: 'Failed to update chat' });
	}
});

app.delete('/api/chats/:chatId', requireAuth, async (req: Request, res: Response) => {
	try {
		const deleted = await ChatStore.delete(req.params.chatId, req.session.userId!);
		if (!deleted) {
			res.status(404).json({ message: 'Failed to delete chat' });
			return;
		}
		res.json({ message: 'Chat deleted' });
	} catch (error) {
		console.error(`[Server] Delete chat error:`, error);
		res.status(500).json({ message: 'Failed to delete chat' });
	}
});

app.post('/api/chats/:chatId/stream', requireAuth, async (req: Request, res: Response) => {
	const { chatId } = req.params;
	const { userPrompt, settings } = req.body;
	const userId = req.session.userId!;

	const chat = await ChatStore.getByChatId(chatId);
	if (!chat || chat.userId !== userId) {
		return res.status(404).json({ message: 'Chat not found' });
	}
	if (!userPrompt?.trim()) {
		return res.status(400).json({ message: 'No prompt provided' });
	}

	const userMessage: Message = {
		role: 'user',
		content: userPrompt,
		timestamp: new Date().toISOString()
	};

	const currentSettings = settings || chat.settings;
	const messagesWithUser = [...chat.messages, userMessage];
	await ChatStore.update(chatId, {
		messages: messagesWithUser,
		settings: currentSettings,
		preview: chat.preview === 'New chat' ? userPrompt.slice(0, 50) : chat.preview
	});

	res.setHeader('Content-Type', 'text/event-stream');
	res.setHeader('Cache-Control', 'no-cache');
	res.setHeader('Connection', 'keep-alive');
	res.setHeader('X-Accel-Buffering', 'no');
	res.flushHeaders();

	let references: Reference[] = [];

	if (currentSettings.professionalMode) {
		references = await DocumentStore.search(
			userPrompt,
			userId,
			currentSettings.topK || 5,
			currentSettings.similarityThreshold || DEFAULT_THRESHOLD
		);

		if (references.length === 0) {
			res.write(`data: ${JSON.stringify({ type: 'content', text: "I don't know based on the provided materials." })}\n\n`);
			res.write('data: [DONE]\n\n');
			res.end();
			return;
		}

		res.write(`data: ${JSON.stringify({ type: 'references', references })}\n\n`);
	}

	const systemPrompt = createSystemPrompt(currentSettings.professionalMode, references.length > 0);
	const ragContext = buildRAGContext(references);

	const abortController = new AbortController();
	let clientDisconnected = false;
	req.on('close', () => {
		console.log(`[Server] Client disconnected for chat ${chatId}, aborting stream`);
		clientDisconnected = true;
		abortController.abort();
	});

	let streamGenerator: AsyncGenerator<string> | null = null;
	let providerName = '';

	if (hasGemini) {
		providerName = 'Gemini';
		streamGenerator = streamGemini(messagesWithUser, systemPrompt, ragContext, abortController.signal);
	} else if (hasOpenAI) {
		providerName = 'OpenAI';
		streamGenerator = streamOpenAI(messagesWithUser, systemPrompt, ragContext, abortController.signal);
	} else {
		console.error('[Server] No LLM API Key found in .env');
		res.write(`data: ${JSON.stringify({ type: 'error', message: 'Server Configuration Error: No API Key found.' })}\n\n`);
		res.write('data: [DONE]\n\n');
		res.end();
		return;
	}

	console.log(`[Server] Streaming response using: ${providerName}`);

	try {
		for await (const chunk of streamGenerator!) {
			if (clientDisconnected) break;
			res.write(`data: ${JSON.stringify({ type: 'content', text: chunk })}\n\n`);
		}
		console.log(`[Server] Stream completed for chat ${chatId}`);
	} catch (error) {
		const err = error as Error;
		if (err.message === 'Aborted') {
			console.log(`[Server] Stream aborted for chat ${chatId}`);
		} else {
			console.error(`[Server] Stream error for chat ${chatId}:`, error);
			res.write(`data: ${JSON.stringify({ type: 'error', message: 'Stream failed: ' + err.message })}\n\n`);
		}
	} finally {
		res.write('data: [DONE]\n\n');
		res.end();
	}
});

// ============================================================================================================
// 14. Document Routes
// ============================================================================================================

app.get('/api/documents/count', requireAuth, async (req: Request, res: Response) => {
	try {
		const { count } = await qdrant.count(CONFIG.qdrant.collections.documents, {
			filter: { must: [{ key: 'userId', match: { value: req.session.userId! } }] }
		});
		res.json({ count });
	} catch (error) {
		res.status(500).json({ message: 'Failed to get documents' });
	}
});

app.delete('/api/documents/delete', requireAuth, async (req: Request, res: Response) => {
	try {
		const success = await DocumentStore.deleteByUserId(req.session.userId!);
		if (!success) {
			res.status(500).json({ message: 'Failed to delete documents' });
			return;
		}
		res.json({ success: true, message: 'Documents deleted successfully' });
	} catch (error) {
		res.status(500).json({ message: 'Failed to delete documents' });
	}
});

app.post('/api/documents/upload', requireAuth, upload, async (req: Request, res: Response) => {
	try {
		const file = (req as Request & { file?: Express.Multer.File }).file;
		if (!file) {
			res.status(400).json({ message: 'No file uploaded' });
			return;
		}
		const userId = req.session.userId!;
		const fileContent = file.buffer.toString('utf-8');
		const lines = fileContent.split('\n');
		const srcId = crypto.randomUUID();
		const createdAt = new Date().toISOString();
		const documents: Document[] = [];
		for (const line of lines) {
			if (!line.trim()) continue;
			try {
				const { title, author, page, content } = JSON.parse(line);
				if (!title || !content) continue;
				documents.push({
					srcId,
					docId: crypto.randomUUID(),
					userId,
					title,
					author: author || 'Unknown',
					page: page || -1,
					content,
					createdAt,
				});
			} catch (error) {
				console.error('[Server] Upload parsing error:', error);
			}
		}
		if (documents.length === 0) {
			res.status(400).json({ message: 'No valid documents found' });
			return;
		}
		const success = await DocumentStore.createBatch(documents);
		if (!success) {
			res.status(500).json({ message: 'Failed to store documents' });
			return;
		}
		res.json({ success: true, message: `Uploaded ${documents.length} documents` });
		console.log(`[Server] Uploaded ${documents.length} documents for user ${req.session.userId!}`);
	} catch (error) {
		console.error(`[Server] Upload error:`, error);
		res.status(500).json({ message: 'Failed to upload documents' });
	}
});

// ============================================================================================================
// 15. Static Files (MUST be after API routes)
// ============================================================================================================

// Serve static files from dist directory
const staticPath = path.resolve(CONFIG.staticDir);
if (fs.existsSync(staticPath)) {
	console.log(`[Server] Serving static files from: ${staticPath}`);
	app.use(express.static(staticPath));
	// NOTE: Use /{*path}, /* is not supported
	app.get('/{*path}', (req: Request, res: Response) => {
		// Don't serve index.html for API routes
		if (req.path.startsWith('/api')) {
			res.status(404).json({ error: 'Not found' });
			return;
		}
		res.sendFile(path.join(staticPath, 'index.html'));
	});
} else {
	console.log(`[Server] Static directory not found: ${staticPath}`);
	console.log(`[Server] Running in API-only mode`);
}

// ============================================================================================================
// 16. Graceful Shutdown & Initialization
// ============================================================================================================

let server: http.Server | null = null;
let isShuttingDown = false;

async function shutdown(signal: string): Promise<void> {
	if (isShuttingDown) return;
	isShuttingDown = true;
	console.log(`\n[Server] Received ${signal}, shutting down...`);
	if (server) {
		await new Promise<void>((resolve) => {
			server!.close(() => {
				console.log('[Server] HTTP server closed');
				resolve();
			});
		});
	}
	console.log('[Server] Cleanup complete.');
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

async function run(): Promise<void> {
	console.log('\n========================================');
	console.log('  RAG Chat Server');
	console.log('========================================\n');

	const cachePath = path.resolve(CONFIG.embedding.cacheDir);
	if (!fs.existsSync(cachePath)) {
		fs.mkdirSync(cachePath, { recursive: true });
	}

	try {
		// For development: reset collections on restart
		// Comment this out in production!
		// await resetAllCollections();

		await initEmbedder();
		await UserStore.init();
		await ChatStore.init();
		await DocumentStore.init();

		// Demo user
		if (!await UserStore.exists('demo')) {
			await UserStore.create({
				userId: crypto.randomUUID(),
				username: 'demo',
				passwordHash: await bcrypt.hash('123456', 10)
			});
			console.log('[Server] Demo user created (demo/123456)');
		}

		server = app.listen(CONFIG.port, CONFIG.host, () => {
			console.log(`\n[Server] Running on http://${CONFIG.host}:${CONFIG.port}`);
			console.log(`[Server] Static files: ${CONFIG.staticDir}`);

			if (hasGemini) console.log(`[Server] Gemini: Active (${CONFIG.llm.gemini.model})`);
			else console.log(`[Server] Gemini: Inactive (Key not found)`);

			if (hasOpenAI) console.log(`[Server] OpenAI: Active (${CONFIG.llm.openai.model})`);
			else console.log(`[Server] OpenAI: Inactive (Key not found)`);

			console.log('\n[Server] Ready to accept connections');
		});
	} catch (error) {
		console.error('[Server] Failed to initialize:', error);
		process.exit(1);
	}
}

run();