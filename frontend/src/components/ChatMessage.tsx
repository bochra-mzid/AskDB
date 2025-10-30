import { Box, Typography, Paper } from '@mui/material';
import type { ChatMessage } from '../types';

interface ChatMessageProps {
	message: ChatMessage;
}

export default function ChatMessage({ message }: ChatMessageProps) {
	return (
		<Box display="flex" flexDirection="column" alignItems={message.type === 'user' ? 'flex-end' : 'flex-start'}>
			<Box maxWidth="75%">
				{message.type === 'user' ? (
					<Paper
						sx={{
							background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
							color: 'white',
							padding: '16px',
							borderRadius: '18px',
							borderBottomRightRadius: '6px',
						}}
					>
						<Typography variant="body1">{message.question}</Typography>
					</Paper>
				) : (
					<Paper
						sx={{
							background: '#1a1a2e',
							border: '1px solid rgba(255, 255, 255, 0.1)',
							borderRadius: '18px',
							borderBottomLeftRadius: '6px',
							padding: '16px',
							display: 'flex',
							flexDirection: 'column',
							gap: '16px',
						}}
					>
						{message.response && (
							<Typography variant="body2" color="#e0e0e0">
								{message.response}
							</Typography>
						)}
						{message.query && (
							<Box display="flex" flexDirection="column" gap={1}>
								<Typography variant="body2" color="#667eea" fontWeight={700}>
									Generated SQL Query
								</Typography>
								<Box
									p={2}
									sx={{
										background: '#0f0f1e',
										border: '1px solid rgba(255, 255, 255, 0.1)',
										borderRadius: '8px',
									}}
								>
									<Typography variant="body2" fontFamily="Fira Code" color="#e0e0e0">
										{message.query}
									</Typography>
								</Box>
							</Box>
						)}
					</Paper>
				)}
			</Box>
			<Typography
				sx={{
					fontSize: '11px',
					color: 'rgba(255, 255, 255, 0.6)',
					marginTop: '8px',
					textAlign: message.type === 'user' ? 'right' : 'left',
				}}
			>
				{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
			</Typography>
		</Box>
	);
}
